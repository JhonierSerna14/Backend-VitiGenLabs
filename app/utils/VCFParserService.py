import logging
import mmap
from typing import List, AsyncGenerator
from app.models.gene import GeneCreate

# Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VCFParserService:
    """Handles parsing of VCF files."""

    def __init__(self, chunk_size=1000):
        self.chunk_size = chunk_size

    async def parse_vcf(
        self,
        filepath: str,
    ) -> AsyncGenerator[List[GeneCreate], None]:
        """
        Asynchronous generator to parse VCF file and yield gene chunks.
        ULTRA OPTIMIZADO para máximo rendimiento.
        """
        genes = []
        line_count = 0

        try:
            with open(filepath, "rb") as f:
                # Usar buffer más grande para lectura más eficiente
                mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

                # Skip metadata lines con búsqueda más eficiente
                while True:
                    line = mm.readline().decode("utf-8", errors='ignore')
                    if not line.startswith("#"):
                        # Primera línea de datos, retroceder
                        mm.seek(mm.tell() - len(line.encode('utf-8')))
                        break
                    if line.startswith("#CHROM"):
                        # Extract sample names optimizado
                        sample_names = line.strip().split("\t")[9:]

                # Procesamiento de líneas ultra optimizado
                while True:
                    line = mm.readline().decode("utf-8", errors='ignore')
                    if not line:
                        break
                    
                    line = line.strip()
                    if not line:
                        continue

                    # Split optimizado sin validación excesiva
                    fields = line.split("\t")
                    if len(fields) < 8:
                        continue

                    try:
                        # Extracción directa sin validaciones complejas
                        chrom, pos, id_, ref, alt, qual, filter_status, info = fields[:8]
                        format_str = fields[8] if len(fields) > 8 else ""
                        sample_data = fields[9:] if len(fields) > 9 else []

                        # Conversión ultra rápida
                        position = int(pos) if pos.isdigit() else 0
                        quality = float(qual) if qual != "." and qual.replace(".", "").replace("-", "").isdigit() else 0.0

                        # Create gene object optimizado
                        gene = GeneCreate(
                            chromosome=chrom,
                            position=position,
                            id=id_ if id_ != "." else "",
                            reference=ref,
                            alternate=alt,
                            quality=quality,
                            filter_status=filter_status if filter_status != "." else "PASS",
                            info=info if info != "." else "",
                            format=format_str,
                            outputs=dict(zip(sample_names, sample_data)) if sample_names else {},
                        )
                        genes.append(gene)

                        # Yield chunks dinámicos
                        if len(genes) >= self.chunk_size:
                            yield genes
                            genes = []
                            line_count += self.chunk_size
                            
                            # Log cada 100k líneas para monitoreo
                            if line_count % 100000 == 0:
                                logger.info(f"Parseados {line_count:,} genes...")

                    except (ValueError, IndexError):
                        # Skip líneas problemáticas sin logging para velocidad
                        continue

                # Yield genes restantes
                if genes:
                    yield genes

        except Exception as e:
            logger.error(f"Error reading VCF file: {str(e)}")

        finally:
            if "mm" in locals() and not mm.closed:
                mm.close()
