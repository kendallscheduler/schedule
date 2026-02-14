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

        # Blocks definition from the website UI
        BLOCKS = [
            {"label": "Block 1", "colspan": 5},
            {"label": "Block 2", "colspan": 5},
            {"label": "Block 3", "colspan": 4},
            {"label": "Block 5", "colspan": 5},
            {"label": "End of year", "colspan": 5},
            {"label": "Block 6", "colspan": 5},
            {"label": "Block 7", "colspan": 5},
            {"label": "Block 8", "colspan": 5},
            {"label": "Block 9", "colspan": 5},
            {"label": "Block 10", "colspan": 8},
        ]
        
        block_edges = set()
        current_sum = 0
        for b in BLOCKS:
            current_sum += b["colspan"]
            block_edges.add(current_sum)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Master Schedule"

        # Styles
        thin_side = Side(border_style="thin", color="cbd5e1")
        thick_side = Side(border_style="medium", color="64748b")
        
        center = Alignment(horizontal="center", vertical="center")
        bold_font = Font(bold=True, size=11, name='Arial')
        header_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        block_fill = PatternFill(start_color="CBD5E1", end_color="CBD5E1", fill_type="solid")

        # Colors (ARGB) - Fix: openpyxl expects hex strings without #, and alpha prefix (FF)
        COLORS = {
            "A": "FF86EFAC", "B": "FF86EFAC", "C": "FF86EFAC", "D": "FF86EFAC", "G": "FF86EFAC",
            "ICU": "FF7DD3FC", "ICU N": "FF38BDF8",
            "CLINIC": "FF93C5FD", "CLINIC *": "FF93C5FD", "ED": "FF93C5FD", "GEN SURG": "FF93C5FD", "TY CLINIC": "FF93C5FD",
            "VACATION": "FFFCA5A5", "NF": "FFE2E8F0", "SWING": "FFC4B5FD",
            "CARDIO": "FFFDBA74", 
            "ID": "FFFEF08A", "NEURO": "FFFEF08A", "GERIATRICS": "FFFEF08A", "ELECTIVE": "FFFEF08A", "ANESTHESIA": "FFFEF08A",
        }
        
        # Set headers
        ws.cell(1, 1).value = "Resident"
        ws.cell(1, 2).value = "PGY"
        ws.cell(1, 3).value = "Track"
        for i in range(1, 4):
            c = ws.cell(1, i)
            c.font = bold_font
            c.alignment = center
            c.fill = header_fill
            c.border = Border(bottom=thin_side, right=thin_side)

        # Draw Block Headers
        curr_col = 4
        for b in BLOCKS:
            ws.merge_cells(start_row=1, start_column=curr_col, end_row=1, end_column=curr_col + b["colspan"] - 1)
            cell = ws.cell(1, curr_col)
            cell.value = b["label"]
            cell.font = bold_font
            cell.alignment = center
            cell.fill = block_fill
            
            # Draw borders for merged block cell
            for c_idx in range(curr_col, curr_col + b["colspan"]):
                top_cell = ws.cell(1, c_idx)
                right_s = thick_side if c_idx == curr_col + b["colspan"] - 1 else thin_side
                top_cell.border = Border(top=thin_side, bottom=thin_side, left=thin_side if c_idx == curr_col else None, right=right_s)
                
            curr_col += b["colspan"]

        # Week Numbers Row
        for w in range(1, 53):
            col = w + 3
            c = ws.cell(2, col, w)
            c.font = Font(bold=True, size=9)
            c.alignment = center
            r_side = thick_side if w in block_edges else thin_side
            c.border = Border(bottom=thin_side, right=r_side)
            c.fill = header_fill

        # Resident Rows
        row_idx = 3
        for r in residents:
            # Info columns
            ws.cell(row_idx, 1, r.name).font = Font(bold=True)
            ws.cell(row_idx, 2, r.pgy).alignment = center
            ws.cell(row_idx, 3, r.cohort.name if r.cohort else ("TY" if r.pgy == "TY" else "")).alignment = center
            
            for i in range(1, 4):
                ws.cell(row_idx, i).border = Border(bottom=thin_side, right=thin_side)

            # Assignment columns
            for w in range(1, 53):
                code = assignments.get(r.id, {}).get(w, "")
                cell = ws.cell(row_idx, w + 3, code)
                cell.alignment = center
                
                # Apply thick border for block edges
                r_side = thick_side if w in block_edges else thin_side
                cell.border = Border(bottom=thin_side, right=r_side)
                
                # Apply identical colors
                if code in COLORS:
                    cell.fill = PatternFill(start_color=COLORS[code], end_color=COLORS[code], fill_type="solid")
                if code in ["ICU N", "NF", "G"]: # Darker text for specific high-contrast needed? 
                    pass # Default is fine

            row_idx += 1

        # Freeze panes
        ws.freeze_panes = "D3"
        
        # Sizing
        ws.column_dimensions["A"].width = 25
        ws.column_dimensions["B"].width = 10
        ws.column_dimensions["C"].width = 15
        for w in range(1, 53):
            ws.column_dimensions[get_column_letter(w + 3)].width = 4.5

        # Totals / Summary Section (to the right of the grid)
        start_totals_col = 56
        totals_headers = ["FLOORS", "ICU", "ICU N", "NF", "SWING", "CLINIC", "ED", "CARDIO", "ELECTIVE", "VACATION"]
        for i, h in enumerate(totals_headers):
            c = ws.cell(2, start_totals_col + i, h)
            c.font = bold_font
            c.alignment = center
            c.fill = header_fill
            c.border = Border(bottom=thin_side, right=thin_side)
            ws.column_dimensions[get_column_letter(start_totals_col + i)].width = 11

        for r_row in range(3, row_idx):
            # FLOORS
            ws.cell(r_row, start_totals_col, f'=COUNTIF(D{r_row}:BC{r_row},"A")+COUNTIF(D{r_row}:BC{r_row},"B")+COUNTIF(D{r_row}:BC{r_row},"C")+COUNTIF(D{r_row}:BC{r_row},"D")+COUNTIF(D{r_row}:BC{r_row},"G")')
            # ICU
            ws.cell(r_row, start_totals_col+1, f'=COUNTIF(D{r_row}:BC{r_row},"ICU")')
            # ICU N
            ws.cell(r_row, start_totals_col+2, f'=COUNTIF(D{r_row}:BC{r_row},"ICU N")')
            # NF
            ws.cell(r_row, start_totals_col+3, f'=COUNTIF(D{r_row}:BC{r_row},"NF")')
            # SWING
            ws.cell(r_row, start_totals_col+4, f'=COUNTIF(D{r_row}:BC{r_row},"SWING")')
            # CLINIC
            ws.cell(r_row, start_totals_col+5, f'=COUNTIF(D{r_row}:BC{r_row},"CLINIC")+COUNTIF(D{r_row}:BC{r_row},"CLINIC *")+COUNTIF(D{r_row}:BC{r_row},"TY CLINIC")')
            # ED
            ws.cell(r_row, start_totals_col+6, f'=COUNTIF(D{r_row}:BC{r_row},"ED")')
            # CARDIO
            ws.cell(r_row, start_totals_col+7, f'=COUNTIF(D{r_row}:BC{r_row},"CARDIO")')
            # ELECTIVE
            ws.cell(r_row, start_totals_col+8, f'=COUNTIF(D{r_row}:BC{r_row},"ELECTIVE")+COUNTIF(D{r_row}:BC{r_row},"ID")+COUNTIF(D{r_row}:BC{r_row},"NEURO")+COUNTIF(D{r_row}:BC{r_row},"GERIATRICS")+COUNTIF(D{r_row}:BC{r_row},"GEN SURG")+COUNTIF(D{r_row}:BC{r_row},"ANESTHESIA")')
            # VACATION
            ws.cell(r_row, start_totals_col+9, f'=COUNTIF(D{r_row}:BC{r_row},"VACATION")')
            # Styling for totals
            for i in range(10):
                cell = ws.cell(r_row, start_totals_col + i)
                cell.border = Border(bottom=thin_side, right=thin_side)
                cell.alignment = center

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
