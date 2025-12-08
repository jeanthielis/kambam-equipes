import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime, timedelta
import csv
import re

class RegistroDefeitosApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Registro de Defeitos - Sistema Offline")
        self.root.geometry("450x600")  # Aumentei um pouco a largura
        self.root.configure(bg='#f0f0f0')
        
        # Configurações
        self.data_file = "registros_defeitos.json"
        self.export_folder = "Relatorios_Defeitos"
        self.target_times = ["05:44", "18:10"]
        
        # Carregar dados
        self.registros = self.carregar_dados()
        
        # Criar interface
        self.criar_interface()
        
        # Agendar exportações
        self.agendar_exportacao()
        
    def carregar_dados(self):
        """Carrega os registros do arquivo JSON"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
        return []
    
    def salvar_dados(self):
        """Salva os registros no arquivo JSON"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.registros, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar dados: {e}")
    
    def criar_interface(self):
        """Cria a interface gráfica"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Cabeçalho
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="Registro de Defeitos", 
                 font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        
        # Botão novo registro
        btn_novo = ttk.Button(header_frame, text="+ Novo Registro (F12)", 
                             command=self.novo_registro)
        btn_novo.pack(side=tk.RIGHT)
        
        # Info de agendamento
        self.lbl_info = ttk.Label(main_frame, text="", font=('Arial', 9))
        self.lbl_info.pack(fill=tk.X, pady=(0, 10))
        
        # Lista de registros
        self.criar_lista_registros(main_frame)
        
        # Frame de controles
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(controls_frame, text="Exportar Agora", 
                  command=self.exportar_agora).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(controls_frame, text="Limpar Tudo", 
                  command=self.limpar_tudo).pack(side=tk.LEFT)
        
        # Bind F12
        self.root.bind('<F12>', lambda e: self.novo_registro())
    
    def criar_lista_registros(self, parent):
        """Cria a lista de registros usando Text widget com scroll"""
        # Frame para a lista
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Label da lista
        ttk.Label(list_frame, text="Registros:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        # Frame com borda para a lista
        border_frame = ttk.Frame(list_frame, relief='sunken', borderwidth=1)
        border_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Text widget com scrollbar - MUDEI AQUI
        self.text_lista = tk.Text(border_frame, wrap=tk.WORD, font=('Arial', 10), 
                                 height=15, padx=5, pady=5, bg='white')
        
        scrollbar = ttk.Scrollbar(border_frame, orient=tk.VERTICAL, command=self.text_lista.yview)
        self.text_lista.configure(yscrollcommand=scrollbar.set)
        
        self.text_lista.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configurar tags para cores
        self.text_lista.tag_configure('normal', foreground='black')
        self.text_lista.tag_configure('baixa', foreground='red')
        self.text_lista.tag_configure('separador', foreground='gray')
        
        # Tornar o text widget readonly
        self.text_lista.config(state=tk.DISABLED)
    
    def converter_qualidade_para_float(self, qualidade_str):
        """Converte string de qualidade (com vírgula) para float"""
        try:
            # Remove % e substitui vírgula por ponto
            limpa = qualidade_str.replace('%', '').replace(',', '.').strip()
            return float(limpa)
        except ValueError:
            return 0.0
    
    def atualizar_lista(self):
        """Atualiza a lista de registros no formato solicitado"""
        # Limpar lista atual
        self.text_lista.config(state=tk.NORMAL)
        self.text_lista.delete(1.0, tk.END)
        
        if not self.registros:
            self.text_lista.insert(tk.END, "Nenhum registro adicionado", 'normal')
            self.text_lista.config(state=tk.DISABLED)
            return
        
        # Ordenar por timestamp (mais recente primeiro)
        registros_ordenados = sorted(self.registros, key=lambda x: x['timestamp'], reverse=True)
        
        # Adicionar registros no formato solicitado
        for i, registro in enumerate(registros_ordenados):
            # Formatar como "12:10 - 98,8%"
            linha_superior = f"{registro['time']} - {registro['qualidade']}"
            linha_inferior = f"{registro['occurrence']}"
            
            # Determinar tag (cor) baseado na qualidade
            qualidade_num = self.converter_qualidade_para_float(registro['qualidade'])
            tag = 'baixa' if qualidade_num < 96 else 'normal'
            
            # Inserir no text widget
            self.text_lista.insert(tk.END, linha_superior + '\n', tag)
            self.text_lista.insert(tk.END, linha_inferior + '\n', 'normal')
            
            # Adicionar separador entre registros (exceto no último)
            if i < len(registros_ordenados) - 1:
                self.text_lista.insert(tk.END, "─" * 50 + '\n', 'separador')
        
        self.text_lista.config(state=tk.DISABLED)
        # Rolagem para o topo
        self.text_lista.see(1.0)
    
    def novo_registro(self):
        """Abre diálogo para novo registro"""
        self.abrir_dialogo_registro()
    
    def aplicar_mascara_qualidade(self, event, entry):
        """Aplica máscara XX,X no campo qualidade"""
        if event.keysym in ['BackSpace', 'Delete', 'Left', 'Right', 'Up', 'Down', 'Tab']:
            return
        
        texto = entry.get()
        
        # Remove tudo que não é dígito
        digitos = re.sub(r'[^\d]', '', texto)
        
        # Limita a 3 dígitos
        if len(digitos) > 3:
            digitos = digitos[:3]
            entry.delete(0, tk.END)
        
        # Aplica formatação XX,X
        if len(digitos) == 0:
            formatado = ""
        elif len(digitos) == 1:
            formatado = digitos
        elif len(digitos) == 2:
            formatado = digitos
        elif len(digitos) == 3:
            formatado = f"{digitos[0:2]},{digitos[2]}"
        
        # Atualiza o campo apenas se mudou
        if entry.get() != formatado:
            entry.delete(0, tk.END)
            entry.insert(0, formatado)
        
        # Salta para ocorrência após 4 caracteres (3 dígitos + vírgula)
        if len(digitos) >= 3:
            if hasattr(self, 'text_ocorrencia'):
                self.text_ocorrencia.focus()
    
    def abrir_dialogo_registro(self, registro_index=None):
        """Abre diálogo para adicionar/editar registro"""
        self.dialog = tk.Toplevel(self.root)
        self.dialog.title("Editar Registro" if registro_index is not None else "Novo Registro")
        self.dialog.geometry("400x300")
        self.dialog.transient(self.root)
        self.dialog.grab_set()
        
        # Frame principal
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Campo qualidade
        ttk.Label(main_frame, text="Qualidade (%):").pack(anchor=tk.W, pady=(0, 5))
        self.entry_qualidade = ttk.Entry(main_frame, font=('Arial', 11), justify='center')
        self.entry_qualidade.pack(fill=tk.X, pady=(0, 15))
        
        # Bind eventos para máscara
        self.entry_qualidade.bind('<KeyRelease>', 
                                lambda e: self.aplicar_mascara_qualidade(e, self.entry_qualidade))
        
        # Campo ocorrência
        ttk.Label(main_frame, text="Ocorrência:").pack(anchor=tk.W, pady=(0, 5))
        self.text_ocorrencia = tk.Text(main_frame, height=6, font=('Arial', 10))
        self.text_ocorrencia.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Bind Enter para salvar no campo ocorrência
        self.text_ocorrencia.bind('<Return>', self.salvar_com_enter)
        self.text_ocorrencia.bind('<Control-Return>', 
                                lambda e: self.text_ocorrencia.insert(tk.INSERT, '\n'))
        
        # Preencher campos se for edição
        self.registro_index_edicao = registro_index
        if registro_index is not None:
            registro = self.registros[registro_index]
            # Remove o % para edição
            qualidade_sem_percent = registro['qualidade'].replace('%', '')
            self.entry_qualidade.insert(0, qualidade_sem_percent)
            self.text_ocorrencia.insert('1.0', registro['occurrence'])
        
        # Frame botões
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Cancelar", 
                  command=self.dialog.destroy).pack(side=tk.LEFT)
        
        ttk.Button(btn_frame, text="Salvar", 
                  command=self.salvar_registro).pack(side=tk.RIGHT)
        
        self.entry_qualidade.focus()
    
    def salvar_com_enter(self, event):
        """Salva o registro quando Enter é pressionado (sem Shift)"""
        if not event.state & 0x1:  # Se Shift não está pressionado
            self.salvar_registro()
            return "break"  # Previne o comportamento padrão do Enter
        return None  # Permite quebra de linha com Shift+Enter
    
    def salvar_registro(self):
        """Salva o registro (usado por ambos: botão e Enter)"""
        qualidade = self.entry_qualidade.get().strip()
        ocorrencia = self.text_ocorrencia.get('1.0', tk.END).strip()
        
        if not qualidade or not ocorrencia:
            messagebox.showwarning("Atenção", "Preencha ambos os campos!")
            return
        
        # Validar formato da qualidade
        if not re.match(r'^\d{1,2},\d$', qualidade) and not re.match(r'^\d{1,3}$', qualidade):
            messagebox.showwarning("Atenção", "Formato de qualidade inválido! Use XX,X")
            return
        
        try:
            # Converter para número (substitui vírgula por ponto)
            qualidade_float = float(qualidade.replace(',', '.'))
            
            if not (0 <= qualidade_float <= 100):
                messagebox.showwarning("Atenção", "Qualidade deve ser entre 0 e 100!")
                return
        except ValueError:
            messagebox.showwarning("Atenção", "Qualidade deve ser um número válido!")
            return
        
        # Formatar qualidade como XX,X% (formato brasileiro)
        qualidade_str = f"{qualidade_float:.1f}%".replace('.', ',')
        
        if self.registro_index_edicao is not None:
            # Editar registro existente
            self.registros[self.registro_index_edicao].update({
                'qualidade': qualidade_str,
                'occurrence': ocorrencia
            })
        else:
            # Novo registro
            agora = datetime.now()
            novo_registro = {
                'time': agora.strftime("%H:%M"),
                'qualidade': qualidade_str,
                'occurrence': ocorrencia,
                'timestamp': agora.timestamp()
            }
            self.registros.append(novo_registro)
        
        self.salvar_dados()
        self.atualizar_lista()
        self.dialog.destroy()
    
    def editar_registro_selecionado(self):
        """Para editar, vamos usar um menu simples por enquanto"""
        # Implementação simplificada - podemos melhorar depois
        messagebox.showinfo("Editar", "Use o menu de contexto com botão direito")
    
    def excluir_registro_selecionado(self):
        """Para excluir, vamos implementar uma função simples"""
        if messagebox.askyesno("Confirmar", "Deseja excluir TODOS os registros?"):
            self.registros = []
            self.salvar_dados()
            self.atualizar_lista()
    
    def limpar_tudo(self):
        """Limpa todos os registros"""
        if self.registros and messagebox.askyesno("Confirmar", 
                                                "Limpar TODOS os registros?"):
            self.registros = []
            self.salvar_dados()
            self.atualizar_lista()
    
    def exportar_agora(self):
        """Exporta registros imediatamente"""
        self.exportar_registros("manual")
        messagebox.showinfo("Sucesso", "Registros exportados com sucesso!")
    
    def exportar_registros(self, tipo_exportacao):
        """Exporta registros para CSV e TXT"""
        if not self.registros:
            return
        
        # Criar pasta de exportação se não existir
        if not os.path.exists(self.export_folder):
            os.makedirs(self.export_folder)
        
        agora = datetime.now()
        data_tag = agora.strftime("%d-%m-%Y")
        hora_tag = agora.strftime("%H%M") if tipo_exportacao == "manual" else tipo_exportacao.replace(':', '')
        
        # Ordenar registros
        registros_ordenados = sorted(self.registros, key=lambda x: x['timestamp'])
        
        # Exportar CSV
        csv_filename = os.path.join(self.export_folder, f"Relatorio_Defeitos_{data_tag}_{hora_tag}.csv")
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Hora', 'Qualidade (%)', 'Ocorrencia'])
            for registro in registros_ordenados:
                writer.writerow([
                    registro['time'],
                    registro['qualidade'],
                    registro['occurrence']
                ])
        
        # Exportar TXT
        txt_filename = os.path.join(self.export_folder, f"Relatorio_Defeitos_{data_tag}_{hora_tag}.txt")
        with open(txt_filename, 'w', encoding='utf-8') as txtfile:
            txtfile.write("RELATÓRIO DE DEFEITOS\n")
            txtfile.write(f"Data do Relatório: {agora.strftime('%d/%m/%Y %H:%M')}\n\n")
            txtfile.write("------------------------------------------------------\n")
            
            for registro in registros_ordenados:
                qualidade_num = self.converter_qualidade_para_float(registro['qualidade'])
                status = " (BAIXA)" if qualidade_num < 96 else ""
                
                txtfile.write(f"HORA: {registro['time']}\n")
                txtfile.write(f"QUALIDADE: {registro['qualidade']}{status}\n")
                txtfile.write(f"OCORRÊNCIA: {registro['occurrence']}\n")
                txtfile.write("------------------------------------------------------\n")
        
        # Limpar registros após exportação automática
        if tipo_exportacao != "manual":
            self.registros = []
            self.salvar_dados()
            self.atualizar_lista()
    
    def agendar_exportacao(self):
        """Agenda as exportações automáticas"""
        self.verificar_exportacao()
        # Verificar a cada minuto
        self.root.after(60000, self.agendar_exportacao)
    
    def verificar_exportacao(self):
        """Verifica se é hora de exportar"""
        agora = datetime.now()
        hora_atual = agora.strftime("%H:%M")
        
        if hora_atual in self.target_times:
            self.exportar_registros(hora_atual)
        
        # Atualizar info na interface
        self.atualizar_info_agendamento()
    
    def atualizar_info_agendamento(self):
        """Atualiza informação de agendamento na interface"""
        agora = datetime.now()
        proxima_export = None
        
        for target in self.target_times:
            hora, minuto = map(int, target.split(':'))
            target_time = datetime(agora.year, agora.month, agora.day, hora, minuto)
            
            if target_time <= agora:
                target_time += timedelta(days=1)
            
            if proxima_export is None or target_time < proxima_export:
                proxima_export = target_time
        
        if proxima_export:
            info = f"Próximo export: {proxima_export.strftime('%d/%m/%Y %H:%M')}"
            self.lbl_info.config(text=info)

def main():
    root = tk.Tk()
    app = RegistroDefeitosApp(root)
    app.atualizar_lista()  # Carregar registros na interface
    root.mainloop()

if __name__ == "__main__":
    main()