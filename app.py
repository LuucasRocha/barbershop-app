from flask import Flask, request, jsonify
from tinydb import TinyDB, Query
from datetime import datetime
from filaAgendamentos import fila_agendamentos

app = Flask(__name__)

# Banco instanciado uma vez
db_barbearia = TinyDB('banco.json')

# Query centralizada
consulta = Query()


@app.route('/api/pesquisaServico', methods=['POST'])
def pesquisa_servico():
    if not request.is_json:
        return jsonify({"erro": "O corpo da requisição deve ser JSON"}), 400

    dados_requisicao = request.get_json()
    tb_servicos = db_barbearia.table('servicos')

    # Lista completa
    todos_servicos = tb_servicos.all()

    # Pesquisa simples
    termo = dados_requisicao.get("servico")
    if termo:
        encontrados = tb_servicos.search(
            consulta.nome.test(lambda x: termo.lower() in x.lower())
        )

        return jsonify({
            "mensagem": "Resultado da pesquisa",
            "servicos_encontrados": encontrados
        }), 200

    # Sem termo de busca → mostra tudo
    return jsonify({
        "quantidade": len(todos_servicos),
        "lista": todos_servicos
    }), 200


@app.route('/api/agendarServico', methods=['POST'])
def agendar_servico():
    if not request.is_json:
        return jsonify({"erro": "O corpo da requisição deve ser JSON"}), 400

    info = request.get_json()

    # Validação simples (não foge do estilo)
    if "cliente" not in info or "servico" not in info:
        return jsonify({"erro": "Dados incompletos"}), 400

    # Carimbo de data
    info["data"] = datetime.now().isoformat()

    tb_agend = db_barbearia.table("agendamentos")

    # ID simples
    info["id"] = len(tb_agend.all()) + 1

    # Salva no banco
    tb_agend.insert(info)

    # Enfileira
    fila_agendamentos.put(info)

    return jsonify({
        "mensagem": "Agendamento realizado",
        "agendamento": info
    }), 200


if __name__ == '__main__':
    app.run(debug=True)
