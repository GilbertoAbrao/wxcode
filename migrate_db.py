import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Carregar .env
load_dotenv()

# Configuração
MONGO_URI = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
SOURCE_DB = "wxkiller"
TARGET_DB = "wxcode"
COLLECTIONS = ["control_types", "products", "stacks"]


def migrate():
    try:
        client = MongoClient(MONGO_URI)
        source = client[SOURCE_DB]
        target = client[TARGET_DB]

        print(f"🔌 Conectado ao MongoDB: {MONGO_URI}")
        print(f"🚀 Migrando de '{SOURCE_DB}' para '{TARGET_DB}'...")
        print("-" * 40)

        # Verifica se o banco de origem existe
        if SOURCE_DB not in client.list_database_names():
            print(f"❌ Banco de dados de origem '{SOURCE_DB}' não encontrado.")
            return

        for col_name in COLLECTIONS:
            # Ler dados da origem
            data = list(source[col_name].find())
            count = len(data)

            if count > 0:
                # Limpar destino antes de inserir
                target[col_name].drop()

                # Inserir dados
                target[col_name].insert_many(data)
                print(f"✅ {col_name}: Migrados {count} registros.")
            else:
                print(f"⚠️  {col_name}: Nenhum registro encontrado na origem.")

        print("-" * 40)
        print("🎉 Migração concluída!")

    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    migrate()
