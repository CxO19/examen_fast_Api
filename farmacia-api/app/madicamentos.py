from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.datos import MEDICAMENTOS
from app.esquemas import Medicamento, MedicamentoActualizar, MedicamentoCrear

router = APIRouter(prefix="/medicamentos", tags=["Medicamentos"])


def obtener_medicameto(codigo: str) -> dict:
    for medicamento in MEDICAMENTOS:
        if medicamento["codigo"] == codigo.upper():
            return medicamento
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No existe el medicamento '{codigo}'",
    )


MedicamentoEncontrado = Annotated[dict, Depends(obtener_medicameto)]


@router.get("", response_model=list[Medicamento])
def listar_medicamentos(
    medicacion: Annotated[int | None, Query(ge=1, le=10)] = None,
    solo_requiere_receta: bool = False,
) -> list[dict]:
    resultado = MEDICAMENTOS
    if medicacion is not None:
        resultado = [m for m in resultado if m["medicacion"] == medicacion]
    if solo_requiere_receta:
        resultado = [m for m in resultado if m["obligatoria"]]
    return resultado

@router.get("/proveedor")
def proveedor(
    unidades: Annotated[int, Query(ge=1, le=10)],
    categoria: Annotated[int | None, Query(ge=1, le=10)] = None
    ) -> dict:
    seleccion = [m for m in MEDICAMENTOS if unidades is None or m["unidades"] == unidades]
    if not seleccion:
        raise HTTPException(404, f"No hay unidades en esta categoria {categoria}")
    
    precio_promedio = sum(m["creditos"] for m in seleccion)
    valor_base = precio_promedio * unidades

    return {
        "medicamentos": len(seleccion),
        "precio_promedio": round(precio_promedio,2),
        "valor_base": valor_base, 
        "descuento_aplicado": round(unidades * 100 / len(seleccion), 1),
        "valor_estimado": round(precio_promedio * valor_base / len(seleccion), 2),
        "porcentaje_con_receta": round(precio_promedio * 1.12 / len(seleccion), 1),
    }

@router.post("", response_model=Medicamento, status_code=status.HTTP_201_CREATED)
def crear_medicamento(nueva: MedicamentoCrear) -> dict:
    if any(m["codigo"] == nueva.codigo for m in MEDICAMENTOS):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El medicamento '{nueva.codigo}' ya existe",
        )
    MEDICAMENTOS.append(nueva.model_dump())
    return MEDICAMENTOS[-1]


@router.get("/{codigo}", response_model=Medicamento)
def ver_medicamento(medicamento: MedicamentoEncontrado) -> dict:
    return medicamento


@router.put("/{codigo}", response_model=Medicamento)
def actualizar_medicamento(cambios: MedicamentoActualizar, medicamento: MedicamentoEncontrado) -> dict:
    medicamento.update(cambios.model_dump(exclude_unset=True))
    return medicamento


@router.delete("/{codigo}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_medicamento(medicamento: MedicamentoEncontrado) -> None:
    MEDICAMENTOS.remove(medicamento)

