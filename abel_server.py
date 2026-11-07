import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from abel import Abel

# Instância global — mantém memória em RAM entre requisições
abel = Abel()


class AbelHandler(BaseHTTPRequestHandler):
    def _responder(self, codigo, dados):
        body = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _pagina_chat(self):
        html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Abel — Assistente IA</title>
<style>
  body { font-family: -apple-system, Segoe UI, Roboto, sans-serif;
         background: #0d1117; color: #e6edf3; margin: 0; padding: 2rem; }
  h1 { color: #58a6ff; margin-bottom: .25rem; }
  .sub { color: #8b949e; margin-bottom: 1.5rem; font-size: .9rem; }
  #chat { max-width: 720px; margin: 0 auto; }
  #log { background: #161b22; border: 1px solid #30363d; border-radius: 8px;
         padding: 1rem; height: 420px; overflow-y: auto; margin-bottom: 1rem; }
  .msg { margin: .5rem 0; padding: .5rem .75rem; border-radius: 6px; }
  .user { background: #1f6feb33; border-left: 3px solid #1f6feb; }
  .abel { background: #23863633; border-left: 3px solid #238636; }
  .quem { font-weight: 600; font-size: .85rem; opacity: .8; margin-bottom: .2rem; }
  form { display: flex; gap: .5rem; }
  input[type=text] { flex: 1; padding: .75rem; border-radius: 6px;
                     border: 1px solid #30363d; background: #0d1117; color: #e6edf3; }
  button { padding: .75rem 1.25rem; border-radius: 6px; border: 0;
           background: #238636; color: #fff; font-weight: 600; cursor: pointer; }
  button:hover { background: #2ea043; }
  .dica { color: #8b949e; font-size: .8rem; margin-top: .75rem; }
</style>
</head>
<body>
<div id="chat">
  <h1>Abel</h1>
  <div class="sub">Assistente pessoal — aprende, lembra e consulta a Wikipedia.</div>
  <div id="log"></div>
  <form id="f">
    <input type="text" id="in" placeholder="Digite algo, senhor..." autocomplete="off" autofocus>
    <button type="submit">Enviar</button>
  </form>
  <div class="dica">Experimente: "o que é fotossíntese", "aprenda que X é Y", "listar".</div>
</div>
<script>
const log = document.getElementById('log');
const f = document.getElementById('f');
const inp = document.getElementById('in');

function add(quem, texto, classe) {
  const d = document.createElement('div');
  d.className = 'msg ' + classe;
  d.innerHTML = '<div class="quem">' + quem + '</div>' + texto.replace(/\\n/g, '<br>');
  log.appendChild(d);
  log.scrollTop = log.scrollHeight;
}

f.addEventListener('submit', async (e) => {
  e.preventDefault();
  const texto = inp.value.trim();
  if (!texto) return;
  add('VOCÊ', texto, 'user');
  inp.value = '';
  add('ABEL', '<em>consultando...</em>', 'abel');
  const ultima = log.lastChild;
  try {
    const r = await fetch('/perguntar?texto=' + encodeURIComponent(texto));
    const j = await r.json();
    ultima.innerHTML = '<div class="quem">ABEL</div>' +
      (j.resposta || j.erro || 'Sem resposta.').replace(/\\n/g, '<br>');
  } catch (err) {
    ultima.innerHTML = '<div class="quem">ABEL</div>Erro de conexão.';
  }
  log.scrollTop = log.scrollHeight;
});
</script>
</body>
</html>"""
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/" or parsed.path == "/chat":
            self._pagina_chat()
            return

        if parsed.path == "/health":
            self._responder(200, {"status": "ok", "nome": "Abel", "versao": "3.0"})
            return

        if parsed.path == "/perguntar":
            params = parse_qs(parsed.query)
            texto = params.get("texto", [""])[0]
            if not texto:
                self._responder(400, {"erro": "Parâmetro 'texto' obrigatório."})
                return
            resposta = abel.processar_mensagem(texto)
            self._responder(200, {"resposta": resposta})
            return

        self._responder(404, {"erro": "Rota não encontrada. Use / ou /perguntar?texto=..."})

    def do_POST(self):
        if self.path != "/perguntar":
            self._responder(404, {"erro": "Rota não encontrada."})
            return
        tamanho = int(self.headers.get("Content-Length", 0))
        corpo = self.rfile.read(tamanho).decode("utf-8")
        try:
            dados = json.loads(corpo)
            texto = dados.get("texto", "")
        except json.JSONDecodeError:
            self._responder(400, {"erro": "JSON inválido."})
            return
        if not texto:
            self._responder(400, {"erro": "Campo 'texto' obrigatório."})
            return
        resposta = abel.processar_mensagem(texto)
        self._responder(200, {"resposta": resposta})

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 8080))
    print(f"Abel v3.0 rodando em http://0.0.0.0:{porta}")
    HTTPServer(("0.0.0.0", porta), AbelHandler).serve_forever()
