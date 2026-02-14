"""Export schedule to Excel matching existing master schedule layout."""
import io
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from models import Resident, ScheduleAssignment, Year, Cohort

router = APIRouter()


@router.get("/excel")
def export_excel(year_id: int, db: Session = Depends(get_db)):
    try:
        """Export to Excel with grid: rows=residents, cols=weeks 1-52."""
        import openpyxl
        from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        import traceback

        residents = (
            db.query(Resident)
            .filter(Resident.year_id == year_id)
            .order_by(Resident.cohort_id, Resident.pgy, Resident.name)
            .all()
        )
        
        assignments = {}
        for a in db.query(ScheduleAssignment).filter(ScheduleAssignment.year_id == year_id).all():
            assignments.setdefault(a.resident_id, {})[a.week_number] = a.rotation_code

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Schedule"

        # Utils
        thin = Side(border_style="thin", color="000000")
        border = Border(top=thin, left=thin, right=thin, bottom=thin)
        center = Alignment(horizontal="center", vertical="center")
        bold = Font(bold=True)

        # Colors (ARGB) - Fix: openpyxl expects hex strings without #, and alpha prefix (FF)
        COLORS = {
            "A": "FF86EFAC", "B": "FF86EFAC", "C": "FF86EFAC", "D": "FF86EFAC", "G": "FF86EFAC",
            "ICU": "FF7DD3FC", "ICU N": "FF38BDF8",
            "CLINIC": "FF93C5FD", "CLINIC *": "FF93C5FD", "ED": "FF93C5FD", "GEN SURG": "FF93C5FD", "TY CLINIC": "FF93C5FD",
            "VACATION": "FFFCA5A5", "NF": "FFE2E8F0", "SWING": "FFC4B5FD",
            "CARDIO": "FFFDBA74", 
            "ID": "FFFEF08A", "NEURO": "FFFEF08A", "GERIATRICS": "FFFEF08A", "ELECTIVE": "FFFEF08A", "ANESTHESIA": "FFFEF08A",
        }
        
        ws.merge_cells("A1:C2")
        ws.cell(1, 1).value = "Resident"
        ws.cell(1, 1).alignment = center
        ws.cell(1, 1).font = bold

        for w in range(1, 53):
            col = w + 3
            c = ws.cell(2, col, w)
            c.alignment = center # Fix: use alignment property assignment, not .element
            c.font = bold
            c.border = border
            if (w - 1) % 4 == 0:
                block_num = (w - 1) // 4 + 1
                ws.cell(1, col, f"Block {block_num}")
                ws.cell(1, col).font = bold
                ws.cell(1, col).alignment = Alignment(horizontal="left")

        row = 3
        for r in residents:
            ws.cell(row, 1, r.name).font = bold
            ws.cell(row, 2, r.pgy)
            ws.cell(row, 3, r.cohort.name if r.cohort else ("TY" if r.pgy == "TY" else ""))
            
            for w in range(1, 53):
                code = assignments.get(r.id, {}).get(w, "")
                cell = ws.cell(row, w + 3, code)
                cell.alignment = center
                cell.border = border
                if code in COLORS:
                    cell.fill = PatternFill(start_color=COLORS[code], end_color=COLORS[code], fill_type="solid")
            
            row += 1

        ws.freeze_panes = "D3"
        
        ws.column_dimensions["A"].width = 20
        ws.column_dimensions["B"].width = 8
        ws.column_dimensions["C"].width = 12
        for w in range(1, 53):
            ws.column_dimensions[get_column_letter(w + 3)].width = 5

        start_col = 56
        headers = ["FLOORS", "ICU", "ICU N", "NF", "SWING", "CLINIC", "ED", "CARDIO", "ELECTIVE", "VACATION"]
        for i, h in enumerate(headers):
            c = ws.cell(2, start_col + i, h)
            c.font = bold
            c.alignment = center
            ws.column_dimensions[get_column_letter(start_col + i)].width = 10

        for r_idx in range(3, row):
            # Formulas match previous logic
            # FLOORS
            ws.cell(r_idx, start_col, f'=COUNTIF(D{r_idx}:BC{r_idx},"A")+COUNTIF(D{r_idx}:BC{r_idx},"B")+COUNTIF(D{r_idx}:BC{r_idx},"C")+COUNTIF(D{r_idx}:BC{r_idx},"D")+COUNTIF(D{r_idx}:BC{r_idx},"G")')
            # ICU
            ws.cell(r_idx, start_col+1, f'=COUNTIF(D{r_idx}:BC{r_idx},"ICU")')
            # ICU N
            ws.cell(r_idx, start_col+2, f'=COUNTIF(D{r_idx}:BC{r_idx},"ICU N")')
            # NF
            ws.cell(r_idx, start_col+3, f'=COUNTIF(D{r_idx}:BC{r_idx},"NF")')
            # SWING
            ws.cell(r_idx, start_col+4, f'=COUNTIF(D{r_idx}:BC{r_idx},"SWING")')
            # CLINIC
            ws.cell(r_idx, start_col+5, f'=COUNTIF(D{r_idx}:BC{r_idx},"CLINIC")+COUNTIF(D{r_idx}:BC{r_idx},"CLINIC *")+COUNTIF(D{r_idx}:BC{r_idx},"TY CLINIC")')
            # ED
            ws.cell(r_idx, start_col+6, f'=COUNTIF(D{r_idx}:BC{r_idx},"ED")')
            # CARDIO
            ws.cell(r_idx, start_col+7, f'=COUNTIF(D{r_idx}:BC{r_idx},"CARDIO")')
            # ELECTIVE
            ws.cell(r_idx, start_col+8, f'=COUNTIF(D{r_idx}:BC{r_idx},"ELECTIVE")+COUNTIF(D{r_idx}:BC{r_idx},"ID")+COUNTIF(D{r_idx}:BC{r_idx},"NEURO")+COUNTIF(D{r_idx}:BC{r_idx},"GERIATRICS")+COUNTIF(D{r_idx}:BC{r_idx},"GEN SURG")+COUNTIF(D{r_idx}:BC{r_idx},"ANESTHESIA")')
            # VACATION
            ws.cell(r_idx, start_col+9, f'=COUNTIF(D{r_idx}:BC{r_idx},"VACATION")')

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=master_schedule.xlsx"},
        )
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=traceback.format_exc())
