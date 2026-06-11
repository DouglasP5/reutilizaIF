import requests
from config import Config
from models import _extrair_nome

_TIMEOUT = 15
_HEADERS = {'Content-Type': 'application/json', 'Accept': 'application/json'}


def _base_url() -> str:
    return Config.SUAP_API_BASE_URL


# O SUAP expõe endpoints diferentes para alunos e servidores.
# O fallback percorre todos até encontrar resposta 200.
def _endpoints_dados():
    base = _base_url()
    return [
        f"{base}/api/rh/eu/",
        f"{base}/api/ensino/meus-dados-aluno/",
        f"{base}/api/v2/rh/eu/",
        f"{base}/api/v2/ensino/meus-dados-aluno/",
    ]


def autenticar_suap(matricula, senha):
    url = f"{_base_url()}/api/token/pair"
    payload = {'username': str(matricula).strip(), 'password': str(senha).strip()}

    try:
        response = requests.post(url, json=payload, headers=_HEADERS, timeout=_TIMEOUT, verify=True)
    except requests.exceptions.ConnectionError:
        return {'sucesso': False, 'erro': 'Não foi possível conectar ao SUAP. Verifique sua conexão.'}
    except requests.exceptions.Timeout:
        return {'sucesso': False, 'erro': 'O servidor SUAP demorou muito para responder.'}
    except requests.exceptions.SSLError:
        return {'sucesso': False, 'erro': 'Erro de certificado SSL. Verifique sua conexão.'}
    except requests.exceptions.RequestException as e:
        return {'sucesso': False, 'erro': f'Erro ao conectar com o SUAP: {e}'}

    if response.status_code == 401:
        try:
            detail = response.json().get('detail', 'Credenciais inválidas')
        except Exception:
            detail = 'Credenciais inválidas. Verifique sua matrícula e senha.'
        return {'sucesso': False, 'erro': detail}

    if response.status_code not in (200, 201):
        try:
            data = response.json()
            msg = data.get('detail') or data.get('message') or data.get('error') or 'Erro ao autenticar'
        except Exception:
            msg = f'Erro {response.status_code}'
        return {'sucesso': False, 'erro': msg}

    try:
        token_data = response.json()
    except ValueError:
        return {'sucesso': False, 'erro': 'Resposta inválida do SUAP'}

    token = token_data.get('access') or token_data.get('token') or token_data.get('access_token')
    if not token:
        return {'sucesso': False, 'erro': 'Token não encontrado na resposta do SUAP'}

    dados_usuario = obter_dados_usuario_suap(token)
    if not dados_usuario:
        return {'sucesso': False, 'erro': 'Não foi possível obter os dados do usuário'}

    return {'sucesso': True, 'token': token, 'dados_usuario': dados_usuario}


def obter_dados_usuario_suap(token):
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}

    for url in _endpoints_dados():
        try:
            response = requests.get(url, headers=headers, timeout=_TIMEOUT, verify=True)
            if response.status_code == 200:
                return _normalizar_dados(response.json())
        except requests.exceptions.RequestException:
            continue

    return None


def _normalizar_dados(dados):
    nome = _extrair_nome(dados)
    if nome:
        dados['nome_usual'] = nome
        dados['nome'] = nome

    foto = (dados.get('foto') or dados.get('url_foto') or
            dados.get('foto_150x200') or dados.get('url_foto_150x200'))
    if foto and not foto.startswith('http'):
        foto = f"https://suap.ifrn.edu.br{foto}"
    if foto:
        dados['foto'] = foto

    return dados
