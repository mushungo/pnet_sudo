import os
import glob
import json

def load_and_print_context():
    """
    Busca, lee e imprime las definiciones de todos los agentes y skills
    para establecer el contexto al inicio de una sesión.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    print("--- CONTEXTO DEL PROYECTO ---")
    print("=" * 30)
    
    # 1. Cargar Agentes
    print("\n--- AGENTES DISPONIBLES ---\n")
    agentes_path = os.path.join(project_root, 'agentes', '*.json')
    agente_files = sorted(glob.glob(agentes_path))
    
    if not agente_files:
        print("No se encontraron definiciones de agentes.")
    else:
        for agent_file in agente_files:
            try:
                with open(agent_file, 'r', encoding='utf-8') as f:
                    # Imprimir el nombre del fichero como cabecera
                    print(f"--- AGENTE: {os.path.basename(agent_file)} ---")
                    # Cargar y re-imprimir el JSON con formato para asegurar legibilidad
                    content = json.load(f)
                    print(json.dumps(content, indent=2, ensure_ascii=False))
                    print("-" * 20)
            except Exception as e:
                print(f"--- ERROR AL LEER {os.path.basename(agent_file)} ---")
                print(str(e))
                print("-" * 20)

    # 2. Cargar Skills
    print("\n--- SKILLS DISPONIBLES ---\n")
    skills_path = os.path.join(project_root, 'skills', '**', '*.md')
    skill_files = sorted(glob.glob(skills_path, recursive=True))

    if not skill_files:
        print("No se encontraron definiciones de skills.")
    else:
        for skill_file in skill_files:
            try:
                with open(skill_file, 'r', encoding='utf-8') as f:
                    relative_path = os.path.relpath(skill_file, os.path.join(project_root, 'skills'))
                    print(f"--- SKILL: {relative_path.replace(os.sep, '/')} ---")
                    content = f.read()
                    print(content)
                    print("-" * 20)
            except Exception as e:
                print(f"--- ERROR AL LEER {os.path.basename(skill_file)} ---")
                print(str(e))
                print("-" * 20)

    print("\n" + "=" * 30)
    print("--- FIN DEL CONTEXTO ---")


if __name__ == "__main__":
    load_and_print_context()
