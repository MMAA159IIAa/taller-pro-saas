from flask import Flask, jsonify

app = Flask(__name__)

# Simular nuestro SaaS central
@app.route("/api/v1/license/check/<int:taller_id>")
def check_license(taller_id):
    # Simulamos que el taller_id = 1 NO HA PAGADO (status: suspendido)
    return jsonify({
        "taller_id": taller_id,
        "taller_name": "Taller Pro Demo",
        "status": "suspendido",
        "mensaje": "⚠️ ALERTA: Su mensualidad no fue procesada por Stripe.\n\nEl acceso a TallerPro ha sido bloqueado remotamente. Por favor contacte a Administración para reanudar el acceso a sus datos."
    })

if __name__ == "__main__":
    print("🚀 [MOCK] Servidor Central SaaS de Prueba Iniciado en el puerto 8000...")
    app.run(port=8000)
