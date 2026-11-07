import urllib.request
import urllib.parse
import json


class WikipediaHelper:
    def __init__(self, idioma="pt"):
        self.idioma = idioma
        self.user_agent = "AbelIA/3.0 (https://github.com/seu-usuario/abel-ia)"

    def _requisitar(self, url):
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        try:
            with urllib.request.urlopen(req, timeout=10) as resposta:
                return json.loads(resposta.read().decode("utf-8"))
        except Exception:
            return None

    def buscar_resumo(self, termo):
        termo_formatado = urllib.parse.quote(termo.strip().replace(" ", "_"))
        url = (f"https://{self.idioma}.wikipedia.org/api/rest_v1/"
               f"page/summary/{termo_formatado}")
        dados = self._requisitar(url)

        if not dados or "extract" not in dados:
            return None

        resumo = dados["extract"].strip()
        if not resumo:
            return None

        if len(resumo) > 500:
            resumo = resumo[:500].rsplit(".", 1)[0] + "."
        return resumo

    def buscar_com_desambiguacao(self, termo):
        resumo = self.buscar_resumo(termo)
        if resumo:
            return resumo

        termo_busca = urllib.parse.quote(termo)
        url = (f"https://{self.idioma}.wikipedia.org/w/api.php"
               f"?action=query&list=search&srsearch={termo_busca}"
               f"&format=json&srlimit=1")
        dados = self._requisitar(url)

        if dados and dados.get("query", {}).get("search"):
            titulo = dados["query"]["search"][0]["title"]
            return self.buscar_resumo(titulo)

        return None
