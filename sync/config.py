import os
from dotenv import load_dotenv

# En local carga las credenciales desde sync/.env o el .env de la raíz del repo.
# En GitHub Actions las variables ya vienen del entorno — load_dotenv no las sobreescribe.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
load_dotenv()  # fallback: .env en el directorio de trabajo

SUPABASE_URL    = os.environ['SUPABASE_URL']
SUPABASE_KEY    = os.environ['SUPABASE_KEY']
QFIELD_USER     = os.environ['QFIELD_USER']
QFIELD_PASSWORD = os.environ['QFIELD_PASSWORD']
PROJECT_NAME    = os.environ['QFIELD_PROJECT_NAME']
BASE_URL        = 'https://app.qfield.cloud/api/v1'
CONTRATO_ID     = os.environ['CONTRATO_ID']
STORAGE_BUCKET  = 'Registro_Obra'
