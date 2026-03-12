import streamlit as st
import grpc
import pandas as pd
import time
import uuid

import carrito_pb2
import carrito_pb2_grpc

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Arcane Reads | Tienda de Pradera", 
    page_icon="🌾", 
    layout="wide",
    initial_sidebar_state="collapsed" 
)

# --- IDENTIFICACIÓN PERSISTENTE DE SESIÓN ---
if "id" in st.query_params:
    st.session_state.cliente_id = st.query_params["id"]
else:
    if 'cliente_id' not in st.session_state:
        nuevo_id = str(uuid.uuid4())
        st.session_state.cliente_id = nuevo_id
        st.query_params["id"] = nuevo_id

# --- INICIALIZACIÓN DE ESTADO ---
if 'estado' not in st.session_state:
    st.session_state.estado = None

if 'version_inventario' not in st.session_state:
    st.session_state.version_inventario = 0

if 'productos_lista' not in st.session_state:
    st.session_state.productos_lista = []

# --- CONFIGURACIÓN DE CONEXIÓN REMOTA ---
url_ngrok_activa = "4.tcp.ngrok.io:15837" 

with st.sidebar:
    st.markdown("### 🌐 Monitoreo Distribuido")
    ip_servidor = st.text_input("Backend URL (ngrok):", value=url_ngrok_activa)
    live_sync = st.toggle("Sincronización en tiempo real", value=True)
    st.divider()
    st.caption(f"ID Cliente: {st.session_state.cliente_id[:8]}")
    st.caption(f"Versión Local: v{st.session_state.version_inventario}")
    if st.button("Limpiar Sesión 🗑️"):
        st.query_params.clear()
        st.session_state.clear()
        st.rerun()

# --- LÓGICA DE COMUNICACIÓN gRPC ---
def llamar_servidor(accion, producto=None, precio=0.0, cantidad=1):
    try:
        with grpc.insecure_channel(ip_servidor) as channel:
            stub = carrito_pb2_grpc.GestorCarritoStub(channel)
            
            if accion == "agregar":
                req = carrito_pb2.ItemRequest(
                    producto=producto, precio=precio, cantidad=cantidad, 
                    cliente_id=st.session_state.cliente_id
                )
                return stub.AgregarItem(req, timeout=5)
            
            elif accion == "eliminar":
                req = carrito_pb2.ItemRequest(
                    producto=producto, precio=0, cantidad=-1, 
                    cliente_id=st.session_state.cliente_id
                )
                return stub.AgregarItem(req, timeout=5)
            
            elif accion == "pagar":
                req = carrito_pb2.VaciarRequest(cliente_id=st.session_state.cliente_id)
                return stub.Pagar(req, timeout=5)
            
            elif accion == "obtener_inventario":
                return stub.ObtenerInventario(carrito_pb2.Empty(), timeout=3)
            
            elif accion == "sincronizar_carrito":
                req = carrito_pb2.ItemRequest(
                    producto="", precio=0, cantidad=0, 
                    cliente_id=st.session_state.cliente_id
                )
                return stub.AgregarItem(req, timeout=5)
                
    except Exception:
        return None

# --- SINCRONIZACIÓN POR EVENTO ---
def sincronizar_estado():
    res_inv = llamar_servidor("obtener_inventario")
    if res_inv and hasattr(res_inv, 'version'):
        if res_inv.version > st.session_state.version_inventario:
            st.session_state.productos_lista = res_inv.productos
            st.session_state.version_inventario = res_inv.version
    
    if st.session_state.estado is None:
        res_cart = llamar_servidor("sincronizar_carrito")
        if res_cart:
            st.session_state.estado = res_cart

sincronizar_estado()

# --- ESTILOS VISUALES ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Lato:wght@300;400;700&display=swap');
    .stApp { background-color: #fdfbf7; color: #4a4a4a; font-family: 'Lato', sans-serif; }
    #MainMenu, footer, header {visibility: hidden;}
    h1, h2, h3 { font-family: 'Cinzel', serif !important; color: #8b7355 !important; }
    
    .custom-navbar { 
        background: rgba(253, 251, 247, 0.9); padding: 1rem 2rem; display: flex; 
        justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(139, 115, 85, 0.2); 
        position: sticky; top: 0; z-index: 999; margin-left: -4rem; margin-right: -4rem; backdrop-filter: blur(10px); 
    }
    
    div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] { 
        background: white; border-radius: 8px; padding: 1.5rem; border: 1px solid rgba(139, 115, 85, 0.1); 
        box-shadow: 0 4px 10px rgba(0,0,0,0.02); transition: all 0.3s ease; 
        position: relative;
    }

    .badge-agotado {
        background-color: #ff4b4b; color: white; padding: 2px 10px; 
        border-radius: 4px; font-weight: bold; font-size: 0.8rem;
        margin-bottom: 10px; display: inline-block;
    }

    /* Botones principales */
    .stButton>button { 
        background: #8b7355; color: white !important; border-radius: 4px; border: none; 
        font-weight: 700; width: 100%; transition: 0.3s; text-transform: uppercase;
    }
    .stButton>button:hover { background: #6b5a42; transform: translateY(-1px); }
    .stButton>button:disabled { background: #d3d3d3 !important; color: #999 !important; }

    /* Mejora estética de los botones de cantidad en el carrito */
    button[key*="min_"], button[key*="add_"] {
        border-radius: 50% !important;
        width: 30px !important;
        height: 30px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background-color: #f5efe6 !important;
        border: 1px solid #d4c4b7 !important;
        color: #8b7355 !important;
    }
    
    button[key*="min_"]:hover, button[key*="add_"]:hover {
        background-color: #8b7355 !important;
        color: white !important;
        border-color: #8b7355 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- NAVBAR ---
st.markdown("""
<div class="custom-navbar">
    <div style="font-family: 'Cinzel'; font-size: 1.5rem; font-weight: 700; color: #8b7355; letter-spacing: 2px;">ARCANE READS</div>
    <div style="color: #8b7355; font-weight: bold; font-family: 'Cinzel';">[ TIENDA DISTRIBUIDA ]</div>
</div>
""", unsafe_allow_html=True)

# --- CARRITO MEJORADO CON PERSISTENCIA ---
col_vacia, col_carro = st.columns([7, 3])
with col_carro:
    items_count = st.session_state.estado.total_articulos if st.session_state.estado else 0
    with st.popover(f"🧺 Mi Bolsa ({items_count})", use_container_width=True):
        st.markdown("### 🧺 Tu Selección")
        if st.session_state.estado and st.session_state.estado.total_articulos > 0:
            for item in st.session_state.estado.desglose:
                st.markdown(f"<div style='color: #8b7355; font-weight: bold; margin-bottom: 5px;'>{item.nombre}</div>", unsafe_allow_html=True)
                c_qty, c_sub = st.columns([0.6, 0.4])
                
                with c_qty:
                    # Controles de cantidad estilizados
                    q1, q2, q3 = st.columns([1, 1, 1])
                    with q1:
                        if st.button("－", key=f"min_{item.nombre}"):
                            res = llamar_servidor("eliminar", producto=item.nombre)
                            if res: st.session_state.estado = res; st.rerun()
                    with q2:
                        st.markdown(f"<div style='text-align:center; font-weight:bold; font-size: 1.1rem; padding-top:2px;'>{item.cantidad}</div>", unsafe_allow_html=True)
                    with q3:
                        precio_u = item.subtotal / item.cantidad
                        if st.button("＋", key=f"add_{item.nombre}"):
                            res = llamar_servidor("agregar", producto=item.nombre, precio=precio_u)
                            if res:
                                if res.exito:
                                    st.session_state.estado = res
                                    st.rerun()
                                else:
                                    st.error("Sin stock")
                with c_sub:
                    st.markdown(f"<div style='text-align:right; color:#8b7355; font-weight:bold; font-size: 1.1rem;'>${item.subtotal:,.2f}</div>", unsafe_allow_html=True)
                st.divider()
                
            st.markdown(f"<div style='text-align: right; margin-bottom: 10px;'><span style='color: #6b6b6b;'>Total:</span> <span style='font-size: 1.5rem; color: #8b7355; font-weight: bold;'>${st.session_state.estado.gran_total:,.2f}</span></div>", unsafe_allow_html=True)
            
            if st.button("Confirmar Pedido 💳", type="primary", use_container_width=True):
                res = llamar_servidor("pagar")
                if res:
                    st.session_state.estado = res
                    st.balloons() # ¡Globos de celebración!
                    time.sleep(1) # Tiempo para ver los globos
                    st.rerun()
        else:
            st.info("Tu bolsa está vacía.")

# --- CATÁLOGO ---
imagenes_mock = {
    "Kindle Paperwhite": "https://images.unsplash.com/photo-1592496001020-d31bd830651f?w=600",
    "The Cruel Prince": "https://covers.openlibrary.org/b/isbn/9780316310277-L.jpg",
    "Fourth Wing": "https://covers.openlibrary.org/b/isbn/9781649374042-L.jpg",
    "A Deadly Education": "https://covers.openlibrary.org/b/isbn/9780593128480-L.jpg",
    "ACOTAR": "https://covers.openlibrary.org/b/isbn/9781619634442-L.jpg",
    "La Reina Roja": "https://covers.openlibrary.org/b/isbn/9780062310637-L.jpg"
}

if not st.session_state.productos_lista:
    st.error("⚠️ Conectando con el servidor gRPC...")
else:
    for i in range(0, len(st.session_state.productos_lista), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(st.session_state.productos_lista):
                p = st.session_state.productos_lista[i + j]
                es_agotado = p.stock <= 0
                img_url = imagenes_mock.get(p.nombre, "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=400")
                
                with cols[j]:
                    if es_agotado:
                        st.markdown('<div class="badge-agotado">AGOTADO</div>', unsafe_allow_html=True)
                        st.markdown(f'<img src="{img_url}" style="width:100%; filter: grayscale(100%); opacity: 0.5; border-radius: 4px;">', unsafe_allow_html=True)
                    else:
                        st.image(img_url, use_container_width=True)
                    
                    st.subheader(p.nombre)
                    st.markdown(f"**Precio:** ${p.precio:,.2f} | **Stock:** {p.stock}")
                    
                    if st.button(f"Añadir", key=f"cat_{p.nombre}", disabled=es_agotado):
                        res = llamar_servidor("agregar", p.nombre, p.precio)
                        if res:
                            st.session_state.estado = res
                            if res.exito:
                                st.toast(f"✅ {p.nombre} añadido!")
                                time.sleep(0.3)
                                st.rerun()

# --- AUTO-REFRESCO ---
if live_sync:
    time.sleep(5) 
    st.rerun()