from flask import Flask, request, jsonify
from tinydb import TinyDB, Query
from datetime import datetime
from filaAgendamentos import fila_agendamentos

app = Flask(__name__)

db_barbearia = TinyDB('banco.json', indent=4) 
consulta = Query()

@app.route('/api/pesquisaServico', methods=['POST'])
def pesquisa_servico():
    if not request.is_json:
        return jsonify({"erro": "O corpo da requisição deve ser JSON"}), 400

    dados_requisicao = request.get_json()
    tb_servicos = db_barbearia.table('servicos')

    todos_servicos = tb_servicos.all()

    termo = dados_requisicao.get("servico")
    if termo:
        encontrados = tb_servicos.search(
            consulta.nome.test(lambda x: termo.lower() in x.lower())
        )

        return jsonify({
            "mensagem": "Resultado da pesquisa",
            "servicos_encontrados": encontrados
        }), 200

 
    return jsonify({
        "quantidade": len(todos_servicos),
        "lista": todos_servicos
    }), 200


@app.route('/api/agendarServico', methods=['POST'])
def agendar_servico():
    if not request.is_json:
        return jsonify({"erro": "O corpo da requisição deve ser JSON"}), 400

    info = request.get_json()

    # Validação
    if "cliente" not in info or "servico" not in info:
        return jsonify({"erro": "Dados incompletos"}), 400

    # Registra a data/hora atual automaticamente
    info["data"] = datetime.now().isoformat()

    # Abre a tabela de agendamentos
    tb_agend = db_barbearia.table("agendamentos")

    # ID simples
    info["id"] = len(tb_agend.all()) + 1

    tb_agend.insert(info)

    fila_agendamentos.put(info)

    return jsonify({
        "mensagem": "Agendamento realizado",
        "agendamento": info
    }), 200

@app.route('/api/cancelarAgendamento', methods=['POST'])
def cancelar_agendamento():
    if not request.is_json:
        return jsonify({"erro": "O corpo da requisição deve ser JSON"}), 400

    dados = request.get_json()
    agendamento_id = dados.get("id")

    if not agendamento_id:
        return jsonify({"erro": "ID do agendamento é obrigatório"}), 400

    tb_agend = db_barbearia.table("agendamentos")

    agendamento = tb_agend.get(consulta.id == agendamento_id)

    if not agendamento:
        return jsonify({"erro": "Agendamento não encontrado"}), 404

    # Remove do banco
    tb_agend.remove(consulta.id == agendamento_id)

    # Remove da fila
    itens_temporarios = []
    while not fila_agendamentos.empty():
        item = fila_agendamentos.get()
        if item.get("id") != agendamento_id:
            itens_temporarios.append(item)

    # Retorna itens para fila
    for item in itens_temporarios:
        fila_agendamentos.put(item)

    return jsonify({
        "mensagem": "Agendamento cancelado com sucesso",
        "agendamento_cancelado": agendamento
    }), 200


if __name__ == '__main__':
    app.run(debug=True)