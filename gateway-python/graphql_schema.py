import strawberry
from typing import Optional, List
from datetime import datetime

import vehiculo_client
import cliente_client
import reserva_client


@strawberry.type
class VehiculoDisponibleType:
    patente: str
    marca: str
    modelo: str
    anio: int
    color: str
    tipo: str
    precioDiario: float


@strawberry.type
class ReservaDetalleType:
    clienteNombre: str
    clienteApellido: str
    vehiculoMarca: str
    vehiculoModelo: str
    patente: str
    fechaHoraInicio: str
    fechaHoraFin: str
    precioDiario: float
    importeTotal: float
    estado: str


@strawberry.type
class HistorialType:
    vehiculoMarca: str
    vehiculoModelo: str
    patente: str
    fechaHoraInicio: str
    fechaHoraFin: str
    cantidadDias: int
    importeTotal: float
    estado: str


# Las reservas que devuelve el Rental Service solo traen clienteId/vehiculoId
# se completan los datos con llamadas a los servicios y se arma la respuesta para la intefaz web
def _enriquecer_reserva(r) -> ReservaDetalleType:
    cliente = cliente_client.obtener_por_id(r.clienteId)
    vehiculo = vehiculo_client.obtener_por_id(r.vehiculoId)
    return ReservaDetalleType(
        clienteNombre=cliente.nombre,
        clienteApellido=cliente.apellido,
        vehiculoMarca=vehiculo.marca,
        vehiculoModelo=vehiculo.modelo,
        patente=vehiculo.patente,
        fechaHoraInicio=r.fechaHoraInicio,
        fechaHoraFin=r.fechaHoraFin,
        precioDiario=r.precioDiario,
        importeTotal=r.importeTotal,
        estado=r.estado,
    )


def _enriquecer_historial(r) -> HistorialType:
    vehiculo = vehiculo_client.obtener_por_id(r.vehiculoId)
    inicio = datetime.fromisoformat(r.fechaHoraInicio)
    fin = datetime.fromisoformat(r.fechaHoraFin)
    dias = max((fin - inicio).days, 1)
    return HistorialType(
        vehiculoMarca=vehiculo.marca,
        vehiculoModelo=vehiculo.modelo,
        patente=vehiculo.patente,
        fechaHoraInicio=r.fechaHoraInicio,
        fechaHoraFin=r.fechaHoraFin,
        cantidadDias=dias,
        importeTotal=r.importeTotal,
        estado=r.estado,
    )


@strawberry.type
class Query:

    @strawberry.field(description="Vehículos disponibles en un rango de fechas, con filtros opcionales de tipo, marca, modelo y precio.")
    def disponibilidad(
            self,
            fechaHoraInicio: str,
            fechaHoraFin: str,
            tipo: Optional[str] = None,
            marca: Optional[str] = None,
            modelo: Optional[str] = None,
            precioMin: Optional[float] = None,
            precioMax: Optional[float] = None,
    ) -> List[VehiculoDisponibleType]:
        vehiculos = vehiculo_client.consultar_disponibilidad(
            fechaHoraInicio, fechaHoraFin, tipo, marca, modelo, precioMin, precioMax
        )
        return [
            VehiculoDisponibleType(
                patente=v.patente, marca=v.marca, modelo=v.modelo, anio=v.anio,
                color=v.color, tipo=v.tipo, precioDiario=v.precioDiario,
            )
            for v in vehiculos
        ]

    @strawberry.field(description="Consulta de reservas. Los clientes ven solo las propias (clienteId); el administrador (esAdmin=true) puede ver todas con cualquier filtro.")
    def reservas(
            self,
            esAdmin: bool,
            clienteId: Optional[int] = None,
            vehiculoId: Optional[int] = None,
            tipoVehiculo: Optional[str] = None,
            estado: Optional[str] = None,
            fechaDesde: Optional[str] = None,
            fechaHasta: Optional[str] = None,
    ) -> List[ReservaDetalleType]:
        reservas = reserva_client.consultar_reservas(
            cliente_id=clienteId or 0, vehiculo_id=vehiculoId or 0,
            tipo_vehiculo=tipoVehiculo, estado=estado,
            fecha_desde=fechaDesde, fecha_hasta=fechaHasta, es_admin=esAdmin,
        )
        return [_enriquecer_reserva(r) for r in reservas]

    @strawberry.field(description="Historial de alquileres (finalizados o cancelados) de un cliente.")
    def historial(self, clienteId: int) -> List[HistorialType]:
        reservas = reserva_client.consultar_historial(clienteId)
        return [_enriquecer_historial(r) for r in reservas]


schema = strawberry.Schema(query=Query)