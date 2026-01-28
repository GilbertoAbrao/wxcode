"""
Testes para o QueryParser.
"""

import pytest
from pathlib import Path

from wxcode.parser.query_parser import QueryParser, QueryInfo


@pytest.fixture
def parser():
    """Fixture do QueryParser."""
    return QueryParser()


def test_extract_parameters_simple(parser):
    """Testa extração de parâmetros simples."""
    sql = """
    SELECT * FROM Cliente
    WHERE id = {ParamID}
    """

    params = parser._extract_parameters(sql)
    assert params == ["ParamID"]


def test_extract_parameters_multiple(parser):
    """Testa extração de múltiplos parâmetros."""
    sql = """
    SELECT * FROM Cliente
    WHERE id = {ParamIDcliente}
    AND empresa = {ParamIDempresa}
    """

    params = parser._extract_parameters(sql)
    assert params == ["ParamIDcliente", "ParamIDempresa"]


def test_extract_parameters_duplicates(parser):
    """Testa que parâmetros duplicados aparecem apenas uma vez."""
    sql = """
    SELECT * FROM Cliente
    WHERE id = {ParamID}
    OR id = {ParamID}
    """

    params = parser._extract_parameters(sql)
    assert params == ["ParamID"]


def test_extract_parameters_none(parser):
    """Testa SQL sem parâmetros."""
    sql = "SELECT * FROM Cliente WHERE id = 123"

    params = parser._extract_parameters(sql)
    assert params == []


def test_extract_tables_from(parser):
    """Testa extração de tabela do FROM."""
    sql = """
    SELECT IDproduto, Nome
    FROM EmpresaProdutos
    WHERE Inativo = 0
    """

    tables = parser._extract_tables(sql)
    assert "EmpresaProdutos" in tables


def test_extract_tables_join(parser):
    """Testa extração de tabelas com JOIN."""
    sql = """
    SELECT c.Nome, p.Produto
    FROM Cliente c
    JOIN Pedido p ON c.ID = p.ClienteID
    """

    tables = parser._extract_tables(sql)
    assert "Cliente" in tables
    assert "Pedido" in tables


def test_extract_tables_multiple_joins(parser):
    """Testa extração de tabelas com múltiplos JOINs."""
    sql = """
    SELECT *
    FROM Cliente
    JOIN Pedido ON Cliente.ID = Pedido.ClienteID
    JOIN Produto ON Pedido.ProdutoID = Produto.ID
    """

    tables = parser._extract_tables(sql)
    assert "Cliente" in tables
    assert "Pedido" in tables
    assert "Produto" in tables


def test_extract_sql_starts_with_select(parser):
    """Testa que SQL extrai corretamente começando com SELECT."""
    text = """
    Some header text
    Linkpay_ADM
    SELECT
    column1, column2
    FROM table1
    """

    sql = parser._extract_sql(text)
    assert "SELECT" in sql
    assert "column1, column2" in sql
    assert "FROM table1" in sql
    assert "Some header text" not in sql


def test_extract_sql_stops_at_marker(parser):
    """Testa que extração para em marcadores de seção."""
    text = """
    SELECT * FROM Cliente
    WHERE id = 1

    Part 2 › Page › FORM_CLIENTE
    This should not be included
    """

    sql = parser._extract_sql(text)
    assert "SELECT * FROM Cliente" in sql
    assert "Part 2" not in sql
    assert "This should not be included" not in sql
