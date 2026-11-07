import os
import re
import difflib
from datetime import datetime

ARQUIVO_MEMORIA = "abel_memoria.txt"
ARQUIVO_HISTORICO = "abel_historico.txt"
ARQUIVO_MARKDOWN = "abel_memoria.md"


class Abel:
    def __init__(self):
        self.memoria = {}
        self.sinonimos = {}
        self.carregar_memoria()

    # ================= Persistência =================
    def carregar_memoria(self):
        if not os.path.exists(ARQUIVO_MEMORIA):
            return
        with open(ARQUIVO_MEMORIA, "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue
                if linha.startswith("SIN|||"):
                    _, orig, canon = linha.split("|||", 2)
                    self.sinonimos[orig.strip().lower()] = canon.strip().lower()
                elif "|||" in linha:
                    chave, valor = linha.split("|||", 1)
                    self.memoria[chave.strip().lower()] = valor.strip()

    def salvar_memoria(self):
        with open(ARQUIVO_MEMORIA, "w", encoding="utf-8") as f:
            for chave, valor in self.memoria.items():
                f.write(f"{chave}|||{valor}\n")
            for orig, canon in self.sinonimos.items():
                f.write(f"SIN|||{orig}|||{canon}\n")

    def registrar_historico(self, remetente, mensagem):
        with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{ts}] {remetente}: {mensagem}\n")

    def exportar_markdown(self):
        """Exporta a memória para um Markdown legível por humanos."""
        linhas = ["# Memória do Abel", ""]
        linhas.append(f"_Exportado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}_")
        linhas.append("")
        linhas.append("## Conhecimentos")
        linhas.append("")
        if self.memoria:
            linhas.append("| Termo | Definição |")
            linhas.append("|-------|-----------|")
            for k in sorted(self.memoria):
                linhas.append(f"| `{k}` | {self.memoria[k]} |")
        else:
            linhas.append("_Nenhum conhecimento registrado._")
        linhas.append("")
        linhas.append("## Sinônimos")
        linhas.append("")
        if self.sinonimos:
            linhas.append("| Alias | Remete a |")
            linhas.append("|-------|----------|")
            for a in sorted(self.sinonimos):
                linhas.append(f"| `{a}` | `{self.sinonimos[a]}` |")
        else:
            linhas.append("_Nenhum sinônimo registrado._")
        linhas.append("")

        with open(ARQUIVO_MARKDOWN, "w", encoding="utf-8") as f:
            f.write("\n".join(linhas))
        return f"Exportado para '{ARQUIVO_MARKDOWN}', senhor."

    # ================= Personalidade JARVIS =================
    def saudacao(self):
        hora = datetime.now().hour
        if hora < 12:
            periodo = "Bom dia"
        elif hora < 18:
            periodo = "Boa tarde"
        else:
            periodo = "Boa noite"
        return f"{periodo}, senhor. Abel à disposição. Como posso ser útil?"

    def despedida(self):
        return "Encerrando sistemas. Foi um prazer, senhor. Até breve."

    def nao_sei(self, termo, sugestao=None):
        base = (f"Receio não possuir informações sobre '{termo}', senhor. "
                f"Se desejar, posso aprender — basta dizer: aprenda que {termo} é ...")
        if sugestao:
            base += f"\n  (Por acaso o senhor quis dizer '{sugestao}'?)"
        return base

    # ================= Normalização e busca =================
    def normalizar(self, termo):
        termo = termo.strip().lower()
        visitados = set()
        while termo in self.sinonimos and termo not in visitados:
            visitados.add(termo)
            termo = self.sinonimos[termo]
        return termo

    def buscar_fuzzy(self, termo):
        """Retorna a chave mais próxima da memória, se houver correspondência razoável."""
        if not self.memoria:
            return None
        candidatos = list(self.memoria.keys())
        matches = difflib.get_close_matches(termo, candidatos, n=1, cutoff=0.6)
        return matches[0] if matches else None

    def buscar_conhecimento(self, termo):
        canon = self.normalizar(termo)
        if canon in self.memoria:
            return canon, self.memoria[canon]
        for tentativa in (canon, termo.strip().lower()):
            proximo = self.buscar_fuzzy(tentativa)
            if proximo:
                return proximo, self.memoria[proximo]
        return None, None

    # ================= Aprendizado =================
    def _sugestao_para_aprendizado(self, chave):
        """Se a chave for parecida com uma existente, sugere a existente."""
        if chave in self.memoria or chave in self.sinonimos:
            return None
        return self.buscar_fuzzy(chave)

    def aprender(self, frase):
        padrao = r"aprenda que (.+?) (?:é|e|são|sao|significa|quer dizer) (.+)"
        match = re.match(padrao, frase, re.IGNORECASE)
        if not match:
            return ("Perdoe-me, senhor, mas não compreendi o formato. "
                    "Sugiro: 'aprenda que X é Y' (ou 'X significa Y').")
        chave_bruta = match.group(1).strip().lower()
        valor = match.group(2).strip()

        # Sugestão de correção antes de gravar
        sugestao = self._sugestao_para_aprendizado(chave_bruta)
        if sugestao:
            return (f"Senhor, '{chave_bruta}' assemelha-se a '{sugestao}', "
                    f"que já possuo em minha base. Devo registrar como novo termo mesmo assim? "
                    f"Se sim, repita o comando confirmando: "
                    f"'confirme aprenda que {chave_bruta} é {valor}'.")

        chave = self.normalizar(chave_bruta)
        self.memoria[chave] = valor
        self.salvar_memoria()
        return f"Anotado, senhor. Registrei que {chave} é {valor}."

    def aprender_confirmado(self, frase):
        """Versão que ignora a sugestão e grava diretamente (após 'confirme')."""
        padrao = r"confirme aprenda que (.+?) (?:é|e|são|sao|significa|quer dizer) (.+)"
        match = re.match(padrao, frase, re.IGNORECASE)
        if not match:
            return "Formato inválido, senhor. Use: 'confirme aprenda que X é Y'."
        chave = self.normalizar(match.group(1))
        valor = match.group(2).strip()
        self.memoria[chave] = valor
        self.salvar_memoria()
        return f"Confirmado e registrado, senhor. '{chave}' agora é '{valor}'."

    def aprender_sinonimo(self, frase):
        padrao = r"(.+?) (?:é|e) (?:sinônimo|sinonimo|o mesmo que) de? (.+)"
        match = re.match(padrao, frase, re.IGNORECASE)
        if not match:
            return "Formato não reconhecido, senhor. Exemplo: 'carro é sinônimo de automóvel'."
        alias = self.normalizar(match.group(1))
        canon = self.normalizar(match.group(2))
        if alias == canon:
            return "Ambos os termos já são equivalentes, senhor."
        self.sinonimos[alias] = canon
        self.salvar_memoria()
        return f"Registrado, senhor. '{alias}' agora remete a '{canon}'."

    # ================= Consulta =================
    def responder(self, frase):
        padrao = r"o que (?:é|e|são|sao|significa|quer dizer) (.+?)\??$"
        match = re.match(padrao, frase, re.IGNORECASE)
        if not match:
            return None
        termo_original = match.group(1).strip().lower()

        partes = re.split(r"\s+e\s+(?:o que (?:é|e|são|sao)\s+)?", termo_original)
        partes = [p.strip() for p in partes if p.strip()]

        respostas = []
        for parte in partes:
            chave, valor = self.buscar_conhecimento(parte)
            if valor is not None:
                nome_exibicao = chave.capitalize()
                if chave != parte:
                    nome_exibicao += f" (referido como '{parte}')"
                respostas.append(f"{nome_exibicao} é {valor}.")
            else:
                sugestao = self.buscar_fuzzy(parte)
                if sugestao:
                    respostas.append(
                        f"Não encontrei '{parte}', senhor. "
                        f"Por acaso o senhor quis dizer '{sugestao}'?"
                    )
                else:
                    respostas.append(self.nao_sei(parte))

        if len(respostas) == 1:
            return respostas[0]
        return "Sobre suas consultas, senhor:\n  • " + "\n  • ".join(respostas)

    def listar(self):
        if not self.memoria and not self.sinonimos:
            return "Minha base de dados está vazia, senhor."
        linhas = []
        if self.memoria:
            linhas.append("Conhecimentos:")
            for k in sorted(self.memoria):
                linhas.append(f"  • {k} → {self.memoria[k]}")
        if self.sinonimos:
            linhas.append("Sinônimos:")
            for a in sorted(self.sinonimos):
                linhas.append(f"  • {a} → {self.sinonimos[a]}")
        return "Eis o que sei até o momento, senhor:\n" + "\n".join(linhas)

    def esquecer(self, frase):
        match = re.match(r"esqueça (.+)", frase, re.IGNORECASE)
        if not match:
            return "Não entendi o que devo esquecer, senhor."
        termo = self.normalizar(match.group(1))
        removido = False
        if termo in self.memoria:
            del self.memoria[termo]
            removido = True
        if termo in self.sinonimos:
            del self.sinonimos[termo]
            removido = True
        self.sinonimos = {a: c for a, c in self.sinonimos.items() if c != termo}
        if removido:
            self.salvar_memoria()
            return f"Feito, senhor. Removi '{termo}' da memória."
        return f"Não encontrei '{termo}' em meus registros, senhor."

    # ================= Loop principal =================
    def conversar(self):
        msg = self.saudacao()
        print("ABEL: " + msg)
        self.registrar_historico("ABEL", msg)

        while True:
            try:
                entrada = input("VOCÊ: ").strip()
            except (EOFError, KeyboardInterrupt):
                fim = self.despedida()
                print("\nABEL: " + fim)
                self.registrar_historico("ABEL", fim)
                break

            if not entrada:
                continue

            self.registrar_historico("VOCÊ", entrada)
            baixo = entrada.lower()

            # saída
            if baixo in ("sair", "exit", "quit", "tchau"):
                print("ABEL: " + self.despedida())
                self.registrar_historico("ABEL", self.despedida())
                break

            # exportação
            elif baixo in ("exportar", "exportar markdown", "salvar md"):
                resposta = self.exportar_markdown()
                print("ABEL: " + resposta)
                self.registrar_historico("ABEL", resposta)

            # confirmação de aprendizado
            elif baixo.startswith("confirme aprenda que"):
                resposta = self.aprender_confirmado(entrada)
                print("ABEL: " + resposta)
                self.registrar_historico("ABEL", resposta)

            # aprendizado de sinônimo
            elif ("sinônimo" in baixo or "sinonimo" in baixo or "o mesmo que" in baixo) and (
                    baixo.startswith("aprenda que") or " sinônimo de " in baixo
                    or " sinonimo de " in baixo or " o mesmo que " in baixo):
                entrada_sin = entrada[len("aprenda que "):] if baixo.startswith("aprenda que") else entrada
                resposta = self.aprender_sinonimo(entrada_sin)
                print("ABEL: " + resposta)
                self.registrar_historico("ABEL", resposta)

            # aprendizado normal
            elif baixo.startswith("aprenda que"):
                resposta = self.aprender(entrada)
                print("ABEL: " + resposta)
                self.registrar_historico("ABEL", resposta)

            # esquecer
            elif baixo.startswith("esqueça") or baixo.startswith("esqueca"):
                resposta = self.esquecer(entrada)
                print("ABEL: " + resposta)
                self.registrar_historico("ABEL", resposta)

            # consulta
            elif (baixo.startswith("o que é") or baixo.startswith("o que e")
                  or baixo.startswith("o que são") or baixo.startswith("o que sao")
                  or baixo.startswith("o que significa")):
                resposta = self.responder(entrada)
                if resposta is None:
                    resposta = self.nao_sei("isso")
                print("ABEL: " + resposta)
                self.registrar_historico("ABEL", resposta)

            # listar
            elif baixo in ("listar", "memória", "memoria", "o que você sabe", "o que voce sabe"):
                resposta = self.listar()
                print("ABEL: " + resposta)
                self.registrar_historico("ABEL", resposta)

            # saudações
            elif any(s in baixo for s in ("olá", "ola", "oi", "bom dia", "boa tarde", "boa noite")):
                resposta = "Olá, senhor. Sistemas operacionais e à sua disposição."
                print("ABEL: " + resposta)
                self.registrar_historico("ABEL", resposta)

            # identidade
            elif "quem é você" in baixo or "seu nome" in baixo or "quem e voce" in baixo:
                resposta = ("Sou Abel, seu assistente pessoal. "
                            "Fui projetado para aprender e lembrar — com a devida elegância.")
                print("ABEL: " + resposta)
                self.registrar_historico("ABEL", resposta)

            else:
                resposta = ("Não tenho certeza de como proceder, senhor. "
                            "Posso aprender algo novo, caso deseje: 'aprenda que X é Y'.")
                print("ABEL: " + resposta)
                self.registrar_historico("ABEL", resposta)


if __name__ == "__main__":
    Abel().conversar()
