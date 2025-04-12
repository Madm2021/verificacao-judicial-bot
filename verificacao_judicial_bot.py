from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import time
import requests

app = Flask(__name__)

WEBHOOK_URL = "https://hook.us1.make.com/7z6l76lh5pvg96rqo8cmtizpcxnfxxen"

def verificar_processo_auxilio_acidente(cpf=None, nome=None):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    driver = webdriver.Chrome(options=options)
    driver.get("https://www.jusbrasil.com.br/busca")

    termo_busca = cpf if cpf else nome
    if not termo_busca:
        return {"status": "erro", "motivo": "CPF ou Nome obrigatório"}

    resultado = {
        "cpf": cpf,
        "nome": nome,
        "status": "❌ Sem Ação",
        "tipo": "",
        "link": "",
        "data": datetime.now().strftime("%d/%m/%Y")
    }

    try:
        input_busca = driver.find_element(By.NAME, "q")
        input_busca.send_keys(termo_busca)
        input_busca.send_keys(Keys.RETURN)
        time.sleep(5)

        resultados = driver.find_elements(By.CSS_SELECTOR, ".sc-cEvuZC a")
        for r in resultados:
            titulo = r.text.lower()
            link = r.get_attribute("href")

            if any(x in titulo for x in ["auxílio acidente", "auxilio acidente", "art. 86", "indeniza", "sequela"]):
                if "inss" in titulo:
                    resultado.update({
                        "status": "✅ Possui Ação",
                        "tipo": "Auxílio Acidente",
                        "link": link
                    })
                    break

        driver.quit()

    except Exception as e:
        driver.quit()
        resultado.update({"status": "erro", "tipo": str(e)})

    # Envia resultado para o Make (opcional)
    try:
        requests.post(WEBHOOK_URL, json=resultado)
    except Exception as err:
        print(f"Erro ao enviar para Make: {err}")

    return resultado

@app.route("/verificar", methods=["POST"])
def api_verificar():
    data = request.get_json()
    cpf = data.get("cpf")
    nome = data.get("nome")
    resultado = verificar_processo_auxilio_acidente(cpf=cpf, nome=nome)
    return jsonify(resultado)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
