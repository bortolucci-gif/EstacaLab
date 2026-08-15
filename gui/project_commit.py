from copy import deepcopy
from gui.validation import validar_cota_vs_sondagem, validar_na_vs_sondagem


def _obter_dimensoes(dados):
    if isinstance(dados.get("dimensoes_estaca"), dict):
        return deepcopy(dados["dimensoes_estaca"])

    D = float(dados.get("D", 0.25))
    forma = dados.get("forma_estaca", "circular")

    if forma == "quadrada":
        return {"lado": D}

    return {"diametro": D}


def confirmar_fundacao_sondagem(
    state,
    dados_fundacao: dict,
    dados_sondagem: dict,
    snapshot_fundacao: dict,
    snapshot_sondagem: dict
) -> bool:

    candidate = deepcopy(state.para_dict())

    dimensoes = _obter_dimensoes(dados_fundacao)
    criterio_ponta = dados_fundacao.get("criterio_ponta_metalica")

    candidate["tipo_estaca"] = dados_fundacao["tipo_estaca"]
    candidate["forma_estaca"] = dados_fundacao["forma_estaca"]
    candidate["dimensoes_estaca"] = dimensoes
    candidate["criterio_ponta_metalica"] = criterio_ponta
    candidate["cota_inicio"] = dados_fundacao["cota_inicio"]

    candidate["camadas"] = dados_sondagem["camadas"]
    candidate["linha_agua"] = dados_sondagem["linha_agua"]
    candidate["solo_sfl"] = dados_sondagem["solo_sfl"]

    validar_cota_vs_sondagem(
        candidate["cota_inicio"],
        candidate["camadas"]
    )

    validar_na_vs_sondagem(
        candidate["linha_agua"],
        candidate["camadas"]
    )

    dimensoes_snapshot = _obter_dimensoes(snapshot_fundacao)
    criterio_snapshot = snapshot_fundacao.get("criterio_ponta_metalica")

    mudou_fundacao = (
        not state.fundacao_preenchida or
        dados_fundacao["tipo_estaca"] != snapshot_fundacao["tipo_estaca"] or
        dados_fundacao["forma_estaca"] != snapshot_fundacao["forma_estaca"] or
        dimensoes != dimensoes_snapshot or
        criterio_ponta != criterio_snapshot or
        dados_fundacao["cota_inicio"] != snapshot_fundacao["cota_inicio"]
    )

    mudou_camadas = (
        dados_sondagem["camadas"]
        != snapshot_sondagem["camadas"]
    )

    mudou_na = (
        dados_sondagem["linha_agua"]
        != snapshot_sondagem["linha_agua"]
    )

    mudou_sfl = (
        dados_sondagem["solo_sfl"]
        != snapshot_sondagem["solo_sfl"]
    )

    mudou_sondagem_geral = mudou_camadas or mudou_sfl
    nenhuma_alteracao = not (
        mudou_fundacao
        or mudou_sondagem_geral
        or mudou_na
    )

    if nenhuma_alteracao:
        return True

    state.tipo_estaca = candidate["tipo_estaca"]
    state.forma_estaca = candidate["forma_estaca"]
    state.dimensoes_estaca = deepcopy(candidate["dimensoes_estaca"])
    state.criterio_ponta_metalica = candidate["criterio_ponta_metalica"]
    state.cota_inicio = candidate["cota_inicio"]

    state.camadas = candidate["camadas"]
    state.linha_agua = candidate["linha_agua"]
    state.solo_sfl = candidate["solo_sfl"]
    state.fundacao_preenchida = True

    state.marcar_projeto_modificado()

    if mudou_fundacao or mudou_sondagem_geral:
        state.df_aoki = state.df_decourt = state.df_teixeira = None
        state.df_monteiro = state.df_berberian = state.df_media = None
        state.df_dimensionamento = {}
        state.df_recalque = None
        state.metodos_media = []

    elif mudou_na:
        state.df_recalque = None

    state.notificar()
    return True