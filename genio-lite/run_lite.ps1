# Startup script for Genio Lite (Antirez Edition)

Write-Host "🚀 Avvio Genio Lite..." -ForegroundColor Cyan

# 1. Installa dipendenze
Write-Host "📦 Installazione dipendenze..."
pip install -r requirements.txt

# 2. Avvia il backend in background
Write-Host "🧠 Avvio Backend (Porta 8001)..."
Start-Process python -ArgumentList "app.py" -WindowStyle Hidden

# 3. Aspetta un attimo che il server parta
Start-Sleep -s 3

# 4. Apri l'interfaccia nel browser
Write-Host "🌐 Apertura Interfaccia..."
Start-Process "index.html"

Write-Host "✅ Genio Lite è pronto!" -ForegroundColor Green
Write-Host "Per chiudere: chiudi la finestra del browser e termina il processo python se necessario."
