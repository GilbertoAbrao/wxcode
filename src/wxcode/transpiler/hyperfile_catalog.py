"""
Catálogo de funções H* do WLanguage.

Categoriza funções HyperFile por comportamento de buffer
e mapeia equivalentes MongoDB/SQLAlchemy.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class BufferBehavior(str, Enum):
    """Comportamento da função em relação ao buffer global."""

    MODIFIES_BUFFER = "modifies"   # Carrega dados no buffer
    READS_BUFFER = "reads"         # Usa dados já no buffer
    PERSISTS_BUFFER = "persists"   # Salva buffer no banco
    INDEPENDENT = "independent"     # Não afeta buffer


@dataclass
class HFunctionInfo:
    """Informação sobre uma função H*."""

    name: str
    behavior: BufferBehavior
    description: str
    mongodb_equivalent: str
    sqlalchemy_equivalent: Optional[str] = None
    needs_llm: bool = False
    notes: Optional[str] = None


# ===========================================================================
# Catálogo de Funções H*
# ===========================================================================

HFUNCTION_CATALOG: dict[str, HFunctionInfo] = {

    # ===================================================================
    # Funções que MODIFICAM o buffer
    # ===================================================================

    'HReadFirst': HFunctionInfo(
        name='HReadFirst',
        behavior=BufferBehavior.MODIFIES_BUFFER,
        description='Posiciona no primeiro registro e carrega no buffer',
        mongodb_equivalent='find().sort(key, 1).limit(1)',
        sqlalchemy_equivalent='select(...).order_by(...).limit(1)',
    ),

    'HReadNext': HFunctionInfo(
        name='HReadNext',
        behavior=BufferBehavior.MODIFIES_BUFFER,
        description='Carrega próximo registro no buffer',
        mongodb_equivalent='cursor.__next__()',
        sqlalchemy_equivalent='next(iterator)',
        needs_llm=True,
        notes='Requer contexto de iteração - transformar em for loop'
    ),

    'HReadPrevious': HFunctionInfo(
        name='HReadPrevious',
        behavior=BufferBehavior.MODIFIES_BUFFER,
        description='Carrega registro anterior no buffer',
        mongodb_equivalent='cursor (reversed)',
        needs_llm=True,
        notes='Requer inversão de ordem ou armazenamento'
    ),

    'HReadLast': HFunctionInfo(
        name='HReadLast',
        behavior=BufferBehavior.MODIFIES_BUFFER,
        description='Posiciona no último registro e carrega no buffer',
        mongodb_equivalent='find().sort(key, -1).limit(1)',
        sqlalchemy_equivalent='select(...).order_by(...desc()).limit(1)',
    ),

    'HReadSeek': HFunctionInfo(
        name='HReadSeek',
        behavior=BufferBehavior.MODIFIES_BUFFER,
        description='Busca registro por chave e carrega no buffer',
        mongodb_equivalent='find_one({"field": value})',
        sqlalchemy_equivalent='select(...).where(...).first()',
    ),

    'HReadSeekFirst': HFunctionInfo(
        name='HReadSeekFirst',
        behavior=BufferBehavior.MODIFIES_BUFFER,
        description='Busca primeiro registro por chave e carrega no buffer',
        mongodb_equivalent='find_one({"field": value})',
        sqlalchemy_equivalent='select(...).where(...).first()',
    ),

    'HReadSeekLast': HFunctionInfo(
        name='HReadSeekLast',
        behavior=BufferBehavior.MODIFIES_BUFFER,
        description='Busca último registro por chave e carrega no buffer',
        mongodb_equivalent='find({"field": value}).sort(..., -1).limit(1)',
        sqlalchemy_equivalent='select(...).where(...).order_by(...desc()).limit(1)',
    ),

    'HRead': HFunctionInfo(
        name='HRead',
        behavior=BufferBehavior.MODIFIES_BUFFER,
        description='Lê registro por número e carrega no buffer',
        mongodb_equivalent='find_one({"_id": record_num})',
        sqlalchemy_equivalent='get(record_id)',
    ),

    'HReset': HFunctionInfo(
        name='HReset',
        behavior=BufferBehavior.MODIFIES_BUFFER,
        description='Limpa buffer para novo registro',
        mongodb_equivalent='{}  # dict vazio',
        sqlalchemy_equivalent='Model()',
    ),

    'HReadNextAll': HFunctionInfo(
        name='HReadNextAll',
        behavior=BufferBehavior.MODIFIES_BUFFER,
        description='Lê próximo registro incluindo deletados',
        mongodb_equivalent='find() (sem filtro de deleted)',
        needs_llm=True,
    ),

    'HReadPreviousAll': HFunctionInfo(
        name='HReadPreviousAll',
        behavior=BufferBehavior.MODIFIES_BUFFER,
        description='Lê registro anterior incluindo deletados',
        mongodb_equivalent='find() reversed (sem filtro de deleted)',
        needs_llm=True,
    ),

    # ===================================================================
    # Funções que LEEM do buffer (sem modificar)
    # ===================================================================

    'HFound': HFunctionInfo(
        name='HFound',
        behavior=BufferBehavior.READS_BUFFER,
        description='Verifica se último read encontrou registro',
        mongodb_equivalent='result is not None',
        sqlalchemy_equivalent='result is not None',
    ),

    'HOut': HFunctionInfo(
        name='HOut',
        behavior=BufferBehavior.READS_BUFFER,
        description='Verifica se ponteiro saiu dos limites',
        mongodb_equivalent='result is None',
        sqlalchemy_equivalent='StopIteration',
    ),

    'HRecNum': HFunctionInfo(
        name='HRecNum',
        behavior=BufferBehavior.READS_BUFFER,
        description='Retorna número do registro atual',
        mongodb_equivalent='doc["_id"]',
        sqlalchemy_equivalent='obj.id',
    ),

    'HRecordToString': HFunctionInfo(
        name='HRecordToString',
        behavior=BufferBehavior.READS_BUFFER,
        description='Converte registro atual para string',
        mongodb_equivalent='json.dumps(doc)',
        sqlalchemy_equivalent='str(obj)',
    ),

    'HRecordToJSON': HFunctionInfo(
        name='HRecordToJSON',
        behavior=BufferBehavior.READS_BUFFER,
        description='Converte registro atual para JSON',
        mongodb_equivalent='json.dumps(doc)',
        sqlalchemy_equivalent='obj.model_dump_json()',
    ),

    # ===================================================================
    # Funções que PERSISTEM o buffer
    # ===================================================================

    'HAdd': HFunctionInfo(
        name='HAdd',
        behavior=BufferBehavior.PERSISTS_BUFFER,
        description='Insere buffer como novo registro',
        mongodb_equivalent='insert_one(data)',
        sqlalchemy_equivalent='session.add(obj)',
    ),

    'HModify': HFunctionInfo(
        name='HModify',
        behavior=BufferBehavior.PERSISTS_BUFFER,
        description='Atualiza registro atual com buffer',
        mongodb_equivalent='update_one({"_id": id}, {"$set": data})',
        sqlalchemy_equivalent='session.commit()',
    ),

    'HDelete': HFunctionInfo(
        name='HDelete',
        behavior=BufferBehavior.PERSISTS_BUFFER,
        description='Deleta registro atual',
        mongodb_equivalent='delete_one({"_id": id})',
        sqlalchemy_equivalent='session.delete(obj)',
    ),

    'HSave': HFunctionInfo(
        name='HSave',
        behavior=BufferBehavior.PERSISTS_BUFFER,
        description='Salva registro (add ou modify conforme contexto)',
        mongodb_equivalent='replace_one(..., upsert=True)',
        sqlalchemy_equivalent='session.merge(obj)',
        needs_llm=True,
        notes='Precisa determinar se é insert ou update'
    ),

    'HCross': HFunctionInfo(
        name='HCross',
        behavior=BufferBehavior.PERSISTS_BUFFER,
        description='Marca registro como crossed/deletado logicamente',
        mongodb_equivalent='update_one(..., {"$set": {"_deleted": True}})',
        sqlalchemy_equivalent='obj.deleted = True',
    ),

    'HWrite': HFunctionInfo(
        name='HWrite',
        behavior=BufferBehavior.PERSISTS_BUFFER,
        description='Escreve registro em posição específica',
        mongodb_equivalent='replace_one({"_id": pos}, data)',
        needs_llm=True,
    ),

    # ===================================================================
    # Funções de FILTRO
    # ===================================================================

    'HFilter': HFunctionInfo(
        name='HFilter',
        behavior=BufferBehavior.INDEPENDENT,
        description='Define filtro ativo na tabela',
        mongodb_equivalent='find(filter_query)',
        sqlalchemy_equivalent='select(...).where(...)',
        needs_llm=True,
        notes='Afeta reads subsequentes'
    ),

    'HDeactivateFilter': HFunctionInfo(
        name='HDeactivateFilter',
        behavior=BufferBehavior.INDEPENDENT,
        description='Desativa filtro ativo',
        mongodb_equivalent='find() # sem filtro',
        sqlalchemy_equivalent='select(...) # sem where',
    ),

    'HActivateFilter': HFunctionInfo(
        name='HActivateFilter',
        behavior=BufferBehavior.INDEPENDENT,
        description='Reativa filtro previamente definido',
        mongodb_equivalent='find(saved_filter)',
        needs_llm=True,
    ),

    # ===================================================================
    # Funções de TRANSAÇÃO
    # ===================================================================

    'HTransactionStart': HFunctionInfo(
        name='HTransactionStart',
        behavior=BufferBehavior.INDEPENDENT,
        description='Inicia transação',
        mongodb_equivalent='session.start_transaction()',
        sqlalchemy_equivalent='session.begin()',
    ),

    'HTransactionEnd': HFunctionInfo(
        name='HTransactionEnd',
        behavior=BufferBehavior.INDEPENDENT,
        description='Finaliza transação com commit',
        mongodb_equivalent='session.commit_transaction()',
        sqlalchemy_equivalent='session.commit()',
    ),

    'HTransactionCancel': HFunctionInfo(
        name='HTransactionCancel',
        behavior=BufferBehavior.INDEPENDENT,
        description='Cancela transação com rollback',
        mongodb_equivalent='session.abort_transaction()',
        sqlalchemy_equivalent='session.rollback()',
    ),

    # ===================================================================
    # Funções de LOCK
    # ===================================================================

    'HLockFile': HFunctionInfo(
        name='HLockFile',
        behavior=BufferBehavior.INDEPENDENT,
        description='Bloqueia tabela inteira',
        mongodb_equivalent='# MongoDB não tem lock de collection',
        needs_llm=True,
        notes='Considerar semáforo ou flag'
    ),

    'HUnlockFile': HFunctionInfo(
        name='HUnlockFile',
        behavior=BufferBehavior.INDEPENDENT,
        description='Desbloqueia tabela',
        mongodb_equivalent='# Liberar semáforo',
        needs_llm=True,
    ),

    'HLockRecNum': HFunctionInfo(
        name='HLockRecNum',
        behavior=BufferBehavior.INDEPENDENT,
        description='Bloqueia registro específico',
        mongodb_equivalent='findOneAndUpdate com lock flag',
        needs_llm=True,
    ),

    'HUnlockRecNum': HFunctionInfo(
        name='HUnlockRecNum',
        behavior=BufferBehavior.INDEPENDENT,
        description='Desbloqueia registro específico',
        mongodb_equivalent='update_one para liberar lock',
        needs_llm=True,
    ),

    # ===================================================================
    # Funções de POSIÇÃO
    # ===================================================================

    'HSavePosition': HFunctionInfo(
        name='HSavePosition',
        behavior=BufferBehavior.INDEPENDENT,
        description='Salva posição atual do cursor',
        mongodb_equivalent='# Salvar _id atual em variável',
        needs_llm=True,
    ),

    'HRestorePosition': HFunctionInfo(
        name='HRestorePosition',
        behavior=BufferBehavior.MODIFIES_BUFFER,
        description='Restaura posição salva do cursor',
        mongodb_equivalent='find_one({"_id": saved_id})',
        needs_llm=True,
    ),

    'HCancelSeek': HFunctionInfo(
        name='HCancelSeek',
        behavior=BufferBehavior.INDEPENDENT,
        description='Cancela busca em andamento',
        mongodb_equivalent='# Não aplicável',
    ),

    # ===================================================================
    # Funções INDEPENDENTES do buffer
    # ===================================================================

    'HExecuteQuery': HFunctionInfo(
        name='HExecuteQuery',
        behavior=BufferBehavior.INDEPENDENT,
        description='Executa query SQL ou QRY',
        mongodb_equivalent='aggregate() ou find()',
        needs_llm=True,
        notes='Requer análise da query SQL'
    ),

    'HExecuteSQLQuery': HFunctionInfo(
        name='HExecuteSQLQuery',
        behavior=BufferBehavior.INDEPENDENT,
        description='Executa query SQL direto',
        mongodb_equivalent='aggregate() ou find()',
        needs_llm=True,
        notes='Requer tradução SQL→MongoDB'
    ),

    'HNbRec': HFunctionInfo(
        name='HNbRec',
        behavior=BufferBehavior.INDEPENDENT,
        description='Conta registros na tabela',
        mongodb_equivalent='count_documents({})',
        sqlalchemy_equivalent='select(func.count(...))',
    ),

    'HCreation': HFunctionInfo(
        name='HCreation',
        behavior=BufferBehavior.INDEPENDENT,
        description='Cria tabela no banco',
        mongodb_equivalent='# MongoDB cria automaticamente',
        sqlalchemy_equivalent='Base.metadata.create_all()',
    ),

    'HCreationIfNotFound': HFunctionInfo(
        name='HCreationIfNotFound',
        behavior=BufferBehavior.INDEPENDENT,
        description='Cria tabela se não existir',
        mongodb_equivalent='# MongoDB cria automaticamente',
        sqlalchemy_equivalent='if not table.exists(): create',
    ),

    'HOpen': HFunctionInfo(
        name='HOpen',
        behavior=BufferBehavior.INDEPENDENT,
        description='Abre tabela para acesso',
        mongodb_equivalent='# MongoDB não requer open',
        sqlalchemy_equivalent='# Já aberto via session',
    ),

    'HClose': HFunctionInfo(
        name='HClose',
        behavior=BufferBehavior.INDEPENDENT,
        description='Fecha tabela',
        mongodb_equivalent='# MongoDB não requer close',
        sqlalchemy_equivalent='# Session gerencia',
    ),

    # ===================================================================
    # Funções ESPECIAIS
    # ===================================================================

    'HAlias': HFunctionInfo(
        name='HAlias',
        behavior=BufferBehavior.INDEPENDENT,
        description='Cria alias para ter múltiplos buffers',
        mongodb_equivalent='# Não necessário - usar variáveis locais',
        notes='Python não precisa de alias - cada query retorna dados independentes'
    ),

    'HChangeName': HFunctionInfo(
        name='HChangeName',
        behavior=BufferBehavior.INDEPENDENT,
        description='Muda nome lógico da tabela',
        mongodb_equivalent='# Usar nome da collection diretamente',
        needs_llm=True,
    ),

    'HChangeConnection': HFunctionInfo(
        name='HChangeConnection',
        behavior=BufferBehavior.INDEPENDENT,
        description='Muda conexão da tabela',
        mongodb_equivalent='# Usar client/database diferente',
        needs_llm=True,
    ),

    'HListFile': HFunctionInfo(
        name='HListFile',
        behavior=BufferBehavior.INDEPENDENT,
        description='Lista tabelas do banco',
        mongodb_equivalent='db.list_collection_names()',
        sqlalchemy_equivalent='inspect(engine).get_table_names()',
    ),

    'HListItem': HFunctionInfo(
        name='HListItem',
        behavior=BufferBehavior.INDEPENDENT,
        description='Lista campos de uma tabela',
        mongodb_equivalent='# Inferir do primeiro documento',
        needs_llm=True,
    ),

    'HListKey': HFunctionInfo(
        name='HListKey',
        behavior=BufferBehavior.INDEPENDENT,
        description='Lista índices de uma tabela',
        mongodb_equivalent='collection.index_information()',
        sqlalchemy_equivalent='inspect(engine).get_indexes(table)',
    ),

    'HDescribeFile': HFunctionInfo(
        name='HDescribeFile',
        behavior=BufferBehavior.INDEPENDENT,
        description='Descreve estrutura da tabela',
        mongodb_equivalent='# Schema inference',
        needs_llm=True,
    ),

    'HCheckStructure': HFunctionInfo(
        name='HCheckStructure',
        behavior=BufferBehavior.INDEPENDENT,
        description='Verifica estrutura da tabela',
        mongodb_equivalent='# Validação de schema',
        needs_llm=True,
    ),

    'HCheckIndex': HFunctionInfo(
        name='HCheckIndex',
        behavior=BufferBehavior.INDEPENDENT,
        description='Verifica integridade do índice',
        mongodb_equivalent='# MongoDB gerencia automaticamente',
    ),

    'HIndex': HFunctionInfo(
        name='HIndex',
        behavior=BufferBehavior.INDEPENDENT,
        description='Reindexa tabela',
        mongodb_equivalent='collection.reindex()',
    ),

    'HFreeQuery': HFunctionInfo(
        name='HFreeQuery',
        behavior=BufferBehavior.INDEPENDENT,
        description='Libera recursos de query',
        mongodb_equivalent='cursor.close()',
    ),

    'HSetPosition': HFunctionInfo(
        name='HSetPosition',
        behavior=BufferBehavior.MODIFIES_BUFFER,
        description='Define posição do cursor por porcentagem',
        mongodb_equivalent='skip(int(total * pct))',
        needs_llm=True,
    ),

    'HChangeDir': HFunctionInfo(
        name='HChangeDir',
        behavior=BufferBehavior.INDEPENDENT,
        description='Muda diretório dos arquivos',
        mongodb_equivalent='# Não aplicável a MongoDB',
    ),
}


# ===========================================================================
# Funções Helper de Lookup
# ===========================================================================

def get_hfunction(name: str) -> Optional[HFunctionInfo]:
    """
    Busca função H* no catálogo (case-insensitive).

    Args:
        name: Nome da função (ex: "HReadFirst", "hreadfirst")

    Returns:
        HFunctionInfo se encontrado, None caso contrário
    """
    # Busca exata
    if name in HFUNCTION_CATALOG:
        return HFUNCTION_CATALOG[name]

    # Busca case-insensitive
    name_lower = name.lower()
    for func_name, func_info in HFUNCTION_CATALOG.items():
        if func_name.lower() == name_lower:
            return func_info

    return None


def get_functions_by_behavior(behavior: BufferBehavior) -> list[HFunctionInfo]:
    """
    Filtra funções por comportamento de buffer.

    Args:
        behavior: Tipo de comportamento desejado

    Returns:
        Lista de funções com o comportamento especificado
    """
    return [
        func for func in HFUNCTION_CATALOG.values()
        if func.behavior == behavior
    ]


def is_buffer_modifying(name: str) -> bool:
    """
    Verifica se função modifica o buffer.

    Args:
        name: Nome da função

    Returns:
        True se a função modifica o buffer
    """
    func = get_hfunction(name)
    return func is not None and func.behavior == BufferBehavior.MODIFIES_BUFFER


def needs_llm_conversion(name: str) -> bool:
    """
    Verifica se função precisa de LLM para conversão.

    Args:
        name: Nome da função

    Returns:
        True se a função precisa de análise LLM
    """
    func = get_hfunction(name)
    return func is not None and func.needs_llm


def get_mongodb_equivalent(name: str) -> Optional[str]:
    """
    Retorna equivalente MongoDB da função.

    Args:
        name: Nome da função

    Returns:
        String com equivalente MongoDB ou None
    """
    func = get_hfunction(name)
    return func.mongodb_equivalent if func else None


def get_all_function_names() -> list[str]:
    """
    Retorna lista de todos os nomes de funções H*.

    Returns:
        Lista de nomes de funções
    """
    return list(HFUNCTION_CATALOG.keys())


def get_functions_needing_llm() -> list[HFunctionInfo]:
    """
    Retorna funções que precisam de LLM para conversão.

    Returns:
        Lista de funções que precisam de LLM
    """
    return [func for func in HFUNCTION_CATALOG.values() if func.needs_llm]
