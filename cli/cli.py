
"""
cli.py — CV Optimizer CLI
Uso sin servidor FastAPI. Analiza, optimiza y genera CV desde terminal.

Uso:
  python cli.py analyze --cv example_cv.json --offer "Buscamos Python developer con Docker y AWS..."
  python cli.py generate --cv example_cv.json --format html
  python cli.py generate --cv example_cv.json --format pdf --offer "..."
  python cli.py bullets --cv example_cv.json
"""

import argparse
import json
import sys
import re
from pathlib import Path

# Asegura imports desde la raíz
sys.path.insert(0, str(Path(__file__).parent))
from app.services.cv_service import AnalysisService
from app.infrastructure.nlp.skills_detector import detect_skills, compare_cv_vs_offer
from app.domain.cv_model import CVProfile, optimize_cv, analyze_bullet_quality
from app.infrastructure.exporters.pdf_generator import ATSPDFGenerator, FPDF_AVAILABLE
from app.infrastructure.exporters.html_generator import generate_html_cv

service = AnalysisService()

# ─── Colores ANSI ─────────────────────────────────────────────────────────────
G  = "\033[92m"   # verde
Y  = "\033[93m"   # amarillo
R  = "\033[91m"   # rojo
B  = "\033[94m"   # azul
M  = "\033[95m"   # magenta
C  = "\033[96m"   # cian
BOLD = "\033[1m"
DIM  = "\033[2m"
RESET = "\033[0m"


def load_cv(path: str) -> CVProfile:
    with open(path, encoding='utf-8') as f:
        return CVProfile.from_dict(json.load(f))


def cmd_analyze(args):
    print(f"\n{BOLD}{B}━━━ CV OPTIMIZER — Análisis ATS ━━━{RESET}\n")
    profile = load_cv(args.cv)
    offer_text = args.offer or (Path(args.offer_file).read_text() if args.offer_file else None)

    if not offer_text:
        print(f"{Y}Sin oferta. Analizando solo el CV...{RESET}")
        cv_skills = detect_skills(profile.to_plain_text())
        _print_skills(cv_skills, "Skills en tu CV")
        return

    print(f"{DIM}Analizando oferta...{RESET}")
    offer_skills = detect_skills(offer_text)
    cv_skills = detect_skills(profile.to_plain_text())
    comparison = compare_cv_vs_offer(cv_skills, offer_skills)

    # Score
    score = comparison['ats_score']
    grade = comparison['grade']
    score_color = G if score >= 65 else Y if score >= 40 else R
    print(f"\n{BOLD}ATS Score: {score_color}{score}/100  [{grade}]{RESET}")
    _print_score_bar(score)

    # Skills
    print(f"\n{G}✅ Skills que coinciden ({len(comparison['matching_tech'])}):{RESET}")
    print("   " + "  ·  ".join(comparison['matching_tech']) if comparison['matching_tech'] else f"   {DIM}Ninguna{RESET}")

    print(f"\n{R}⚠️  Skills faltantes ({len(comparison['missing_tech'])}):{RESET}")
    print("   " + "  ·  ".join(comparison['missing_tech']) if comparison['missing_tech'] else f"   {G}¡Ninguna! 🎉{RESET}")

    print(f"\n{B}💡 Recomendaciones:{RESET}")
    for rec in comparison['recommendations']:
        print(f"   → {rec}")

    if offer_skills.get('seniority'):
        print(f"\n{M}   Nivel buscado: {offer_skills['seniority'].upper()}{RESET}")
    if offer_skills.get('years_required'):
        print(f"{Y}   Experiencia requerida: {offer_skills['years_required']}+ años{RESET}")


def cmd_generate(args):
    print(f"\n{BOLD}{B}━━━ CV OPTIMIZER — Generando CV ━━━{RESET}\n")
    profile = load_cv(args.cv)
    offer_text = args.offer or (Path(args.offer_file).read_text() if hasattr(args, 'offer_file') and args.offer_file else None)
    fmt = args.format

    if offer_text and args.optimize:
        print(f"{DIM}Optimizando CV para la oferta...{RESET}")
        offer_skills = detect_skills(offer_text)
        cv_skills = detect_skills(profile.to_plain_text())
        comparison = compare_cv_vs_offer(cv_skills, offer_skills)
        profile, promoted, soft_suggested = optimize_cv(
            profile, comparison['missing_tech'], comparison['missing_soft']
        )
        if promoted:
            print(f"{G}Skills promovidas al CV: {', '.join(promoted)}{RESET}")
        score = comparison['ats_score']
        print(f"{B}ATS Score estimado: {score}/100{RESET}")

    name_slug = re.sub(r'[^\w\s-]', '', profile.contact.name).strip().replace(' ', '_') or 'CV'
    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)

    if fmt == 'html':
        html = generate_html_cv(profile)
        out = out_dir / f"cv_{name_slug}.html"
        out.write_text(html, encoding='utf-8')
        print(f"{G}✅ HTML generado: {out}{RESET}")
        print(f"{DIM}   Abre en el navegador y usa Ctrl+P → Guardar como PDF{RESET}")

    elif fmt == 'pdf':
        if not FPDF_AVAILABLE:
            print(f"{R}fpdf2 no instalado. Ejecuta: pip install fpdf2{RESET}")
            sys.exit(1)
        out_path = out_dir / f"cv_{name_slug}.pdf"
        gen = ATSPDFGenerator(profile)
        pdf_bytes = gen.generate()  # Obtiene los bytes
        with open(out_path, "wb") as f:
            f.write(pdf_bytes)  # Guarda el archivo físico
        print(f"{G}✅ PDF generado: {out_path}{RESET}")

    elif fmt == 'json':
        out = out_dir / f"cv_{name_slug}.json"
        out.write_text(profile.to_json(), encoding='utf-8')
        print(f"{G}✅ JSON exportado: {out}{RESET}")


    elif fmt == 'autofill':

        # 1. Llamamos al servicio

        response = service.linkedin_autofill(profile.to_json())

        # 2. Extraemos el contenido (viene como bytes) y lo convertimos a un dict de Python

        import json

        data_dict = json.loads(response.body.decode('utf-8'))

        # 3. Lo guardamos con formato "pretty print" (indentado) para que sea legible

        autofill_data_pretty = json.dumps(data_dict, ensure_ascii=False, indent=2)

        out = out_dir / f"autofill_{name_slug}.json"

        out.write_text(autofill_data_pretty, encoding='utf-8')

        print(f"{G}✅ Autofill JSON generado: {out}{RESET}")

        print(f"\n{BOLD}Datos para LinkedIn / HiringRoom:{RESET}")

        print(autofill_data_pretty)


def cmd_bullets(args):
    print(f"\n{BOLD}{B}━━━ CV OPTIMIZER — Calidad de Bullets ━━━{RESET}\n")
    profile = load_cv(args.cv)
    all_bullets = []
    for exp in profile.experience:
        for b in exp.bullets:
            all_bullets.append((exp.company, b))

    if not all_bullets:
        print(f"{Y}No hay bullets de experiencia en el CV.{RESET}")
        return

    scores = []
    for company, bullet in all_bullets:
        q = analyze_bullet_quality(bullet)
        scores.append(q['score'])
        color = G if q['score'] >= 70 else Y if q['score'] >= 45 else R
        print(f"{color}[{q['score']:3d}]{RESET} {DIM}{company}{RESET}")
        print(f"      {bullet[:90]}{'...' if len(bullet)>90 else ''}")
        for issue in q['issues']:
            print(f"      {Y}→ {issue}{RESET}")
        print()

    avg = sum(scores) / len(scores)
    avg_color = G if avg >= 70 else Y if avg >= 45 else R
    print(f"{BOLD}Promedio: {avg_color}{avg:.0f}/100{RESET}")


def _print_skills(skills_data: dict, title: str):
    print(f"\n{BOLD}{title}:{RESET}")
    for cat, items in skills_data.get('tech_skills', {}).items():
        print(f"  {B}{cat.upper()}{RESET}: {', '.join(items)}")
    if skills_data.get('soft_skills'):
        print(f"  {M}SOFT{RESET}: {', '.join(skills_data['soft_skills'][:6])}")


def _print_score_bar(score: float):
    filled = int(score / 5)
    bar = "█" * filled + "░" * (20 - filled)
    color = G if score >= 65 else Y if score >= 40 else R
    print(f"  {color}[{bar}]{RESET}")


def main():
    parser = argparse.ArgumentParser(
        prog="cv-optimizer",
        description="CV Optimizer CLI — ATS sin IA costosa"
    )
    sub = parser.add_subparsers(dest='cmd')

    # analyze
    p_analyze = sub.add_parser('analyze', help='Analiza CV vs oferta')
    p_analyze.add_argument('--cv', required=True, help='Ruta al JSON del CV')
    p_analyze.add_argument('--offer', help='Texto de la oferta (entrecomillado)')
    p_analyze.add_argument('--offer-file', help='Archivo .txt con la oferta')

    # generate
    p_gen = sub.add_parser('generate', help='Genera CV en HTML, PDF o JSON')
    p_gen.add_argument('--cv', required=True)
    p_gen.add_argument('--format', choices=['html','pdf','json','autofill'], default='html')
    p_gen.add_argument('--offer', help='Texto de oferta para optimizar')
    p_gen.add_argument('--offer-file', help='Archivo .txt con la oferta')
    p_gen.add_argument('--no-optimize', dest='optimize', action='store_false', default=True)

    # bullets
    p_bullets = sub.add_parser('bullets', help='Evalúa calidad de bullets')
    p_bullets.add_argument('--cv', required=True)

    args = parser.parse_args()

    if args.cmd == 'analyze':
        cmd_analyze(args)
    elif args.cmd == 'generate':
        cmd_generate(args)
    elif args.cmd == 'bullets':
        cmd_bullets(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
