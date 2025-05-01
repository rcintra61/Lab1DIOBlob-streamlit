import streamlit as st
from azure.storage.blob import BlobServiceClient
import os
import pymssql
import uuid
from dotenv import load_dotenv

load_dotenv()

blobConnectionString = os.getenv('BLOB_CONNECTION_STRING')
blobContainerName = os.getenv('BLOB_CONTAINER_NAME')
blobAccountName = os.getenv('BLOB_ACCOUNT_NAME')

SQL_SERVER = os.getenv('SQL_SERVER')
SQL_DATABASE = os.getenv('SQL_DATABASE')
SQL_USER = os.getenv('SQL_USER')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')

st.title('Cadastro de Produtos')

product_name = st.text_input('Nome do Produto')
product_price = st.number_input('Preço do Produto', min_value=0.0, format='%.2f')
product_description = st.text_area('Descrição do Produto')
product_image = st.file_uploader('Imagem do Produto', type=['jpg', 'png', 'jpeg'])

def upload_blob(file):
    try:
        blob_service_client = BlobServiceClient.from_connection_string(blobConnectionString)
        container_client = blob_service_client.get_container_client(blobContainerName)
        blob_name = str(uuid.uuid4()) + "_" + file.name
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(file.read(), overwrite=True)
        image_url = f"https://{blobAccountName}.blob.core.windows.net/{blobContainerName}/{blob_name}"
        st.write(f"✅ Imagem enviada: {image_url}")
        return image_url
    except Exception as e:
        st.error(f"Erro no upload da imagem: {e}")
        return None

def insert_product(name, price, description, image):
    try:
        image_url = upload_blob(image)
        if image_url is None:
            st.error("Erro ao enviar imagem, produto não será salvo.")
            return False

        conn = pymssql.connect(server=SQL_SERVER, user=SQL_USER, password=SQL_PASSWORD, database=SQL_DATABASE)
        cursor = conn.cursor()
        sql = "INSERT INTO Produtos (nome, preco, descricao, imagem_url) VALUES (%s, %s, %s, %s)"
        st.write("Executando SQL:", sql)
        st.write("Com valores:", (name, price, description, image_url))
        cursor.execute(sql, (name, price, description, image_url))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir produto: {e}")
        return False

def list_products():
    try:
        conn = pymssql.connect(server=SQL_SERVER, user=SQL_USER, password=SQL_PASSWORD, database=SQL_DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT nome, preco, descricao, imagem_url FROM Produtos")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        st.error(f"Erro ao listar produtos: {e}")
        return []

if st.button('Salvar Produto'):
    if not product_name or not product_description or not product_image:
        st.warning('Preencha todos os campos e envie uma imagem.')
    else:
        if insert_product(product_name, product_price, product_description, product_image):
            st.success('Produto salvo com sucesso!')
        else:
            st.error('Erro ao salvar o produto.')

st.header('Produtos Cadastrados')

if st.button('Listar Produtos'):
    produtos = list_products()
    if not produtos:
        st.info("Nenhum produto cadastrado ainda.")
    else:
        for produto in produtos:
            st.subheader(produto[0])
            st.write(f"Preço: R${produto[1]:.2f}")
            st.write(f"Descrição: {produto[2]}")
            st.image(produto[3], width=300)
