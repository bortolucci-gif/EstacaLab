"""
EstacaLab — Estado global compartilhado entre todas as telas.
Nenhum cálculo é realizado aqui — apenas armazenamento de dados.
"""

import os
import json
import logging
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)

def get_config_path() -> str:
    appdata = os.environ.get('APPDATA')
    if appdata:
        path = os.path.join(appdata, "EstacaLab")
    else:
        path = os.path.expanduser("~/.EstacaLab")
    return os.path.join(path, "config.json")

def load_user_config() -> dict:
    path = get_config_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            dados = json.load(f)
            return dados if isinstance(dados, dict) else {}
    except Exception as e:
        logger.warning(f"Não foi possível carregar as preferências locais: {e}")
        return {}

def save_user_config(responsavel: str, registro: str):
    path = get_config_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        config = load_user_config()
        config["responsavel_tecnico"] = responsavel
        config["registro_profissional"] = registro
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Erro ao salvar configurações do usuário: {e}")


class AppState:
    """
    Singleton que centraliza todos os dados de entrada e resultados calculados.
    Todas as telas leem e escrevem nesta instância.
    """

    def __init__(self):
        self._callbacks = []
        self.reset()
        self.aplicar_defaults_usuario()

    def aplicar_defaults_usuario(self):
        config = load_user_config()
        self.responsavel_tecnico = config.get("responsavel_tecnico", "")
        self.registro_profissional = config.get("registro_profissional", "")

    def reset(self):
        # ── Controle de Dirty State ────────────────────────────
        self.alteracoes_pendentes: set = set()
        self.projeto_modificado: bool = False

        # ── Dados da Fundação ──────────────────────────────────
        self.fundacao_preenchida: bool = False
        self.tipo_estaca: str = "Escavada mecanicamente sem lama"
        self.forma_estaca: str = "circular"
        self.dimensoes_estaca: dict = {"diametro": 0.25}
        self.criterio_ponta_metalica: Optional[str] = None
        self.cota_inicio: float = -1.0
        self.linha_agua: Optional[float] = None
        self.solo_sfl: bool = False

        # ── Sondagem SPT ──────────────────────────────────────
        # Cada camada: {'cota': -1, 'nspt': 0.0, 'cod_solo': 31}
        self.camadas: list = []

        # ── Mapa de Pilares ───────────────────────────────────
        # Cada pilar: {'Pilar': 'P1', 'Carga (kN)': 100}
        self.lista_pilares: list = []

        # ── Resultados calculados ─────────────────────────────
        self.df_aoki:      Optional[pd.DataFrame] = None
        self.df_decourt:   Optional[pd.DataFrame] = None
        self.df_teixeira:  Optional[pd.DataFrame] = None
        self.df_monteiro:  Optional[pd.DataFrame] = None
        self.df_berberian: Optional[pd.DataFrame] = None
        self.df_media:     Optional[pd.DataFrame] = None

        self.df_dimensionamento: dict = {}
        self.df_recalque: Optional[pd.DataFrame] = None

        # ── Metadados do Projeto ──────────────────────────────
        import datetime
        self.nome_projeto: str          = "Novo Projeto"
        self.obra_name: str             = ""
        self.local_obra: str            = ""
        self.responsavel_tecnico: str   = ""
        self.registro_profissional: str = ""
        self.data_analise: str          = datetime.date.today().strftime("%d/%m/%Y")
        self.observacoes: str           = ""

        self.metodos_selecionados = ["aoki", "decourt", "teixeira", "monteiro", "berberian"]
        self.metodos_media: list = []

    # Compatibilidade temporária com telas antigas que ainda usam state.D
    @property
    def D(self) -> float:
        if self.forma_estaca in ["circular", "franki"]:
            return float(self.dimensoes_estaca.get("diametro", 0.0))

        if self.forma_estaca == "quadrada":
            return float(self.dimensoes_estaca.get("lado", 0.0))

        return 0.0

    @D.setter
    def D(self, valor):
        valor = float(valor)

        if not hasattr(self, "dimensoes_estaca"):
            self.dimensoes_estaca = {}

        if self.forma_estaca == "quadrada":
            self.dimensoes_estaca["lado"] = valor
        else:
            self.dimensoes_estaca["diametro"] = valor

    def marcar_projeto_modificado(self):
        self.projeto_modificado = True

    def marcar_projeto_salvo(self):
        self.projeto_modificado = False

    # ─────────────────────────────────────────────────────────
    # Gerenciamento de Alterações Não Salvas
    # ─────────────────────────────────────────────────────────
    def marcar_pendente(self, secao: str):
        self.alteracoes_pendentes.add(secao)

    def marcar_salvo(self, secao: str):
        self.alteracoes_pendentes.discard(secao)

    def tem_pendencias(self, secoes: list = None) -> bool:
        if not secoes:
            return len(self.alteracoes_pendentes) > 0
        return any(s in self.alteracoes_pendentes for s in secoes)

    def obter_pendencias(self, secoes: list = None) -> set:
        if not secoes:
            return self.alteracoes_pendentes.copy()
        return {s for s in secoes if s in self.alteracoes_pendentes}

    # ─────────────────────────────────────────────────────────
    # Helpers de conversão entre camadas e listas dos métodos
    # ─────────────────────────────────────────────────────────
    def get_lista_tipo_solo(self) -> list:
        return [c['cod_solo'] for c in self.camadas]

    def get_lista_nspt(self) -> list:
        return [c['nspt'] for c in self.camadas]

    def num_camadas(self) -> int:
        return len(self.camadas)

    def profundidade_total(self) -> float:
        return float(len(self.camadas))

    def nspt_medio(self) -> float:
        vals = [c['nspt'] for c in self.camadas if c['nspt'] > 0]
        return round(sum(vals) / len(vals), 1) if vals else 0.0

    def calculos_disponiveis(self) -> bool:
        return self.df_aoki is not None

    def dimensionamento_disponivel(self) -> bool:
        return bool(self.df_dimensionamento)

    def recalque_disponivel(self) -> bool:
        return self.df_recalque is not None

    # ─────────────────────────────────────────────────────────
    # Reatividade
    # ─────────────────────────────────────────────────────────
    def registrar_callback(self, fn):
        if fn not in self._callbacks:
            self._callbacks.append(fn)

    def desregistrar_callback(self, fn):
        if fn in self._callbacks:
            self._callbacks.remove(fn)

    def notificar(self):
        for fn in self._callbacks:
            try:
                fn()
            except Exception:
                logger.exception("Erro ao executar callback do AppState: %r", fn)

    # ─────────────────────────────────────────────────────────
    # Persistência
    # ─────────────────────────────────────────────────────────
    def para_dict(self) -> dict:
        return {
            "schema_version": 2,
            "nome_projeto": self.nome_projeto,
            "obra_name": self.obra_name,
            "local_obra": self.local_obra,
            "responsavel_tecnico": self.responsavel_tecnico,
            "registro_profissional": self.registro_profissional,
            "data_analise": self.data_analise,
            "observacoes": self.observacoes,

            "tipo_estaca": self.tipo_estaca,
            "forma_estaca": self.forma_estaca,
            "fundacao_preenchida": self.fundacao_preenchida,
            "dimensoes_estaca": self.dimensoes_estaca.copy(),
            "criterio_ponta_metalica": self.criterio_ponta_metalica,

            # Mantido temporariamente para compatibilidade
            "D": self.D,

            "cota_inicio": self.cota_inicio,
            "linha_agua": self.linha_agua,
            "solo_sfl": self.solo_sfl,
            "camadas": self.camadas,
            "lista_pilares": self.lista_pilares,
            "metodos_selecionados": self.metodos_selecionados,
        }

    def de_dict(self, norm: dict):
        self.nome_projeto = norm["nome_projeto"]
        self.obra_name = norm["obra_name"]
        self.local_obra = norm["local_obra"]
        self.responsavel_tecnico = norm["responsavel_tecnico"]
        self.registro_profissional = norm["registro_profissional"]
        self.data_analise = norm["data_analise"]
        self.observacoes = norm["observacoes"]

        self.tipo_estaca = norm["tipo_estaca"]
        self.forma_estaca = norm["forma_estaca"]
        self.fundacao_preenchida = norm["fundacao_preenchida"]
        self.dimensoes_estaca = norm["dimensoes_estaca"].copy()
        self.criterio_ponta_metalica = norm["criterio_ponta_metalica"]

        self.cota_inicio = norm["cota_inicio"]
        self.linha_agua = norm["linha_agua"]
        self.solo_sfl = norm["solo_sfl"]
        self.camadas = norm["camadas"]
        self.lista_pilares = norm["lista_pilares"]
        self.metodos_selecionados = norm["metodos_selecionados"]

        # Limpa resultados ao abrir novo projeto
        self.df_aoki = self.df_decourt = self.df_teixeira = None
        self.df_monteiro = self.df_berberian = self.df_media = None
        self.df_dimensionamento = {}
        self.df_recalque = None
        self.metodos_media = []

        self.alteracoes_pendentes.clear()
        self.marcar_projeto_salvo()

    def salvar_json(self, caminho: str):
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(self.para_dict(), f, ensure_ascii=False, indent=2)
        self.marcar_projeto_salvo()


def normalizar_dados_projeto(dados) -> dict:
    import datetime

    if not isinstance(dados, dict):
        raise ValueError("O formato do arquivo não é um dicionário válido.")

    sv = dados.get("schema_version")

    if sv is None:
        sv = 0

    if not isinstance(sv, int) or sv < 0:
        raise ValueError("schema_version malformado ou inválido.")

    if sv > 2:
        raise ValueError(
            "Este projeto foi criado por uma versão mais recente do "
            "EstacaLab e não pode ser aberto com segurança nesta versão."
        )

    hoje = datetime.date.today().strftime("%d/%m/%Y")

    tipo_estaca = str(
        dados.get(
            "tipo_estaca",
            "Escavada mecanicamente sem lama"
        )
    )

    forma_estaca = str(
        dados.get(
            "forma_estaca",
            "circular"
        )
    )

    criterio_ponta_metalica = dados.get(
        "criterio_ponta_metalica"
    )

    # Projetos novos
    if isinstance(dados.get("dimensoes_estaca"), dict):
        dimensoes_estaca = {}

        for chave, valor in dados["dimensoes_estaca"].items():
            try:
                valor = float(valor)
            except (TypeError, ValueError):
                raise ValueError(
                    f"Dimensão inválida para '{chave}'."
                )

            if valor <= 0:
                raise ValueError(
                    f"A dimensão '{chave}' deve ser maior que zero."
                )

            dimensoes_estaca[str(chave)] = valor

    # Compatibilidade com projetos antigos
    else:
        D_antigo = float(dados.get("D", 0.25))

        if D_antigo <= 0:
            raise ValueError("O valor antigo de D deve ser maior que zero.")

        if tipo_estaca in [
            "Franki de fuste apiloado",
            "Franki de fuste vibrado"
        ]:
            forma_estaca = "franki"
            dimensoes_estaca = {
                "diametro": D_antigo
            }

        elif tipo_estaca == "Metálica":
            raise ValueError(
                "Este projeto antigo possui uma estaca metálica definida "
                "somente por D. Informe novamente as dimensões do perfil I ou H."
            )

        elif tipo_estaca in ["Barrete", "Escavada (Barrete)"]:
            raise ValueError(
                "Este projeto antigo possui um barrete definido somente por D. "
                "Informe novamente a largura e o comprimento da seção."
            )

        elif forma_estaca.lower() == "quadrada":
            forma_estaca = "quadrada"
            dimensoes_estaca = {
                "lado": D_antigo
            }

        else:
            forma_estaca = "circular"
            dimensoes_estaca = {
                "diametro": D_antigo
            }

    if criterio_ponta_metalica not in [
        None,
        "area_real",
        "retangulo_envolvente"
    ]:
        raise ValueError(
            "Critério de ponta da estaca metálica inválido."
        )

    norm = {
        "nome_projeto": str(dados.get("nome_projeto", "Projeto")),
        "obra_name": str(dados.get("obra_name", "")),
        "local_obra": str(dados.get("local_obra", "")),
        "responsavel_tecnico": str(dados.get("responsavel_tecnico", "")),
        "registro_profissional": str(dados.get("registro_profissional", "")),
        "data_analise": str(dados.get("data_analise", hoje)),
        "observacoes": str(dados.get("observacoes", "")),

        "tipo_estaca": tipo_estaca,
        "forma_estaca": forma_estaca,
        "dimensoes_estaca": dimensoes_estaca,
        "criterio_ponta_metalica": criterio_ponta_metalica,

        "cota_inicio": float(dados.get("cota_inicio", -1.0)),
        "linha_agua": (
            float(dados.get("linha_agua"))
            if dados.get("linha_agua") is not None
            else None
        ),
        "solo_sfl": bool(dados.get("solo_sfl", False)),
        "fundacao_preenchida": bool(dados.get("fundacao_preenchida", True)),
    }

    # Camadas
    camadas_raw = dados.get("camadas", [])

    if not isinstance(camadas_raw, list):
        raise ValueError("'camadas' deve ser uma lista.")

    norm["camadas"] = []

    for c in camadas_raw:
        if not isinstance(c, dict):
            raise ValueError("Item de camada inválido.")

        norm["camadas"].append({
            "cota": float(c.get("cota", 0)),
            "nspt": float(c.get("nspt", 0)),
            "cod_solo": int(c.get("cod_solo", 31))
        })

    # Pilares
    pilares_raw = dados.get("lista_pilares", [])

    if not isinstance(pilares_raw, list):
        raise ValueError("'lista_pilares' deve ser uma lista.")

    norm["lista_pilares"] = []

    for p in pilares_raw:
        if not isinstance(p, dict):
            raise ValueError("Item de pilar inválido.")

        norm["lista_pilares"].append({
            "Pilar": str(p.get("Pilar", "P")),
            "Carga (kN)": float(p.get("Carga (kN)", 0))
        })

    # Métodos selecionados
    metodos_raw = dados.get(
        "metodos_selecionados",
        ["aoki", "decourt", "teixeira", "monteiro", "berberian"]
    )

    if not isinstance(metodos_raw, list):
        raise ValueError("'metodos_selecionados' deve ser uma lista.")

    norm["metodos_selecionados"] = [
        str(m) for m in metodos_raw
    ]

    return norm


# Instância global
state = AppState()