from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from calc.money_code.calculator import calculate as money_calc
from calc.life_code.calculator import calculate as life_calc
from calc.destiny_path.calculator import calculate as destiny_calc
from calc.birth_decoding.calculator import calculate as birth_decoding_calc
from calc.pythagoras_square.calculator import calculate as pythagoras_calc
from calc.prognosis.calculator import calculate as prognosis_calc


router = APIRouter(prefix="/calculators", tags=["calculators"])


class CalcRequest(BaseModel):
    birth_date: str  # format 'dd.mm.yyyy'


CALC_MAP = {
    "money_code": money_calc,
    "life_code": life_calc,
    "destiny_path": destiny_calc,
    "birth_decoding": birth_decoding_calc,
    "pythagoras_square": pythagoras_calc,
    "prognosis": prognosis_calc,
}


@router.post("/{name}")
async def run_calculator(name: str, payload: CalcRequest):
    if name not in CALC_MAP:
        raise HTTPException(status_code=404, detail="Calculator not found")
    try:
        result_html = CALC_MAP[name](payload.birth_date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"result_html": result_html}