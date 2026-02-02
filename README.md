# 💰 Gestor Financeiro Pessoal

Aplicativo web para controle financeiro pessoal, desenvolvido em Python com **Streamlit** e integrado ao **Google Sheets**.

Permite lançar ganhos e despesas, visualizar gráficos de orçamento e acompanhar a evolução do patrimônio (investimentos) ao longo do ano.

## ✨ Funcionalidades

* **Lançamentos Fáceis:** Adicione e remova despesas em uma interface amigável.
* **Dashboards:** Gráficos de pizza e barras automáticos.
* **Evolução Patrimonial:** Acompanhe o crescimento dos seus investimentos mês a mês.
* **100% Nuvem:** Dados salvos diretamente no Google Sheets.

---

## 🚀 Como rodar o projeto localmente

Siga estes passos para rodar o aplicativo no seu computador:

### 1. Clone o repositório
Abra o terminal e baixe os arquivos:

```bash
git clone [https://github.com/SEU_USUARIO/NOME_DO_REPO.git](https://github.com/SEU_USUARIO/NOME_DO_REPO.git)
cd NOME_DO_REPO

### 2. Crie um ambiente virtual
Isso isola as bibliotecas do projeto para não bagunçar seu Python:

No Windows:

Bash

python -m venv venv
.\venv\Scripts\activate
No Linux ou Mac:

Bash

python3 -m venv venv
source venv/bin/activate
### 3. Instale as dependências
Instale o Streamlit, Pandas e as outras bibliotecas necessárias:

Bash

pip install -r requirements.txt
### 4. 🔑 Configuração das Senhas (Importante!)
O arquivo de senhas não vem junto com o código (por segurança). Você precisa criá-lo manualmente.

Na pasta raiz do projeto, crie uma pasta chamada .streamlit.

Dentro dela, crie um arquivo chamado secrets.toml.

Cole suas credenciais do Google Cloud dentro dele:



[connections.gsheets]
spreadsheet = "LINK_DA_SUA_PLANILHA"
worksheet = "Dados_App"
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "..."
client_email = "..."
client_id = "..."
auth_uri = "[https://accounts.google.com/o/oauth2/auth](https://accounts.google.com/o/oauth2/auth)"
token_uri = "[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)"
auth_provider_x509_cert_url = "[https://www.googleapis.com/oauth2/v1/certs](https://www.googleapis.com/oauth2/v1/certs)"
client_x509_cert_url = "..."

### 5. Execute o aplicativo
Com tudo configurado, rode o comando:

Bash

streamlit run app.py
O navegador abrirá automaticamente no endereço http://localhost:8501.

## 🚀 Deploy no Streamlit Cloud

Para publicar o app online:

1. **Faça upload do código** para um repositório público no GitHub (excluindo o arquivo `.streamlit/secrets.toml` - ele já está no `.gitignore`).

2. **Acesse o Streamlit Cloud** em [share.streamlit.io](https://share.streamlit.io) e conecte seu repositório GitHub.

3. **Configure as Secrets:**
   - No painel do app no Streamlit Cloud, vá em "Settings" > "Secrets".
   - Cole as credenciais do Google Sheets no formato TOML.
   - **Importante:** A `private_key` deve ter as quebras de linha representadas por `\n` (não use aspas triplas como no arquivo local).
   - Exemplo de como deve ficar a `private_key`:
     ```
     private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCy1izrfM0xdyLm\n...\n-----END PRIVATE KEY-----"
     ```
   - **Nota:** As secrets no Streamlit Cloud são definidas como variáveis de ambiente, não como arquivos.

4. **Deploy:** Clique em "Deploy" e aguarde a publicação.

**Nota:** O arquivo `.streamlit/secrets.toml` funciona apenas localmente. Para produção, use sempre as secrets do painel do Streamlit Cloud.

🛠️ Tecnologias
Python

Streamlit

Pandas

Plotly

Google Sheets API

Desenvolvido por Gilmar Ribeiro dos Santos.




