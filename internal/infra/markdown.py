import os

class MarkdownReportRepository:
    """
    Implementacion de persistencia de informes en archivos markdown
    Cumple con el protocolo ReportRepository del dominio
    """

    def save_report(self, content: str,output: str = "./reports", filename: str = "report_crtsh.md"):
        """
        Guarda el informe en un archivo markdown
        """
        try:

            os.makedirs(output, exist_ok=True)

            filepath = os.path.join(output, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print("Reporte guardado en: ", filepath)
        except IOError as e:
            print(f"Error al guardar el reporte: {e}")
            raise e