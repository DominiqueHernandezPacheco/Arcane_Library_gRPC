import grpc
from concurrent import futures
import time
import threading
from pyngrok import ngrok 

import carrito_pb2
import carrito_pb2_grpc

# Inventario Global con Versión
class AlmacenGlobal:
    def __init__(self):
        self.productos = {
            "Kindle Paperwhite": {"precio": 2599.0, "stock": 10},
            "The Cruel Prince": {"precio": 450.0, "stock": 5},
            "Fourth Wing": {"precio": 490.0, "stock": 2},
            "A Deadly Education": {"precio": 380.0, "stock": 4},
            "ACOTAR": {"precio": 420.0, "stock": 3},
            "La Reina Roja": {"precio": 390.0, "stock": 5}
        }
        self.version = 1
        self.lock = threading.Lock()

    def actualizar_stock(self, nombre, cantidad):
        with self.lock:
            if nombre in self.productos and self.productos[nombre]["stock"] >= cantidad:
                self.productos[nombre]["stock"] -= cantidad
                self.version += 1 # Cambio detectado
                return True
            return False

almacen = AlmacenGlobal()

class GestorCarritoServicer(carrito_pb2_grpc.GestorCarritoServicer):
    def __init__(self):
        self.carritos = {}

    def ObtenerInventario(self, request, context):
        lista_productos = []
        for nombre, info in almacen.productos.items():
            lista_productos.append(carrito_pb2.ProductoStock(
                nombre=nombre, stock=info["stock"], precio=info["precio"]
            ))
        return carrito_pb2.InventarioResponse(productos=lista_productos, version=almacen.version)

    def AgregarItem(self, request, context):
        if almacen.actualizar_stock(request.producto, request.cantidad):
            cid = request.cliente_id
            if cid not in self.carritos: self.carritos[cid] = {}
            
            p = request.producto
            if p in self.carritos[cid]:
                self.carritos[cid][p]['cantidad'] += request.cantidad
            else:
                self.carritos[cid][p] = {'precio': request.precio, 'cantidad': request.cantidad}
            
            print(f"[OK] Cliente {cid[:4]} -> {p}. Stock: {almacen.productos[p]['stock']}")
            return self._generar_res(cid, f"✅ {p} añadido", True)
        
        return self._generar_res(request.cliente_id, "❌ Sin stock", False)

    def Pagar(self, request, context):
        cid = request.cliente_id
        if cid in self.carritos: self.carritos[cid].clear()
        return self._generar_res(cid, "💰 Pago procesado", True)

    def _generar_res(self, cid, msg, exito):
        items = []
        total_art, total_cash = 0, 0.0
        carro = self.carritos.get(cid, {})
        for n, i in carro.items():
            sub = i['cantidad'] * i['precio']
            total_art += i['cantidad']
            total_cash += sub
            items.append(carrito_pb2.ItemDetalle(nombre=n, cantidad=i['cantidad'], subtotal=sub))
        return carrito_pb2.CarritoResponse(mensaje=msg, total_articulos=total_art, gran_total=total_cash, desglose=items, exito=exito)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    carrito_pb2_grpc.add_GestorCarritoServicer_to_server(GestorCarritoServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    
    # Configuración de ngrok
    ngrok.set_auth_token("3AV2vlkQ8hF2BCzHjFFRTtBMGGi_7MtJfjQ7CUwkuch9XV948") 
    tunel = ngrok.connect(50051, "tcp")
    print(f"\n🚀 SERVIDOR ACTIVO\n🌍 URL: {tunel.public_url.replace('tcp://', '')}\n")
    
    try:
        while True: time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
        ngrok.kill()

if __name__ == '__main__':
    serve()