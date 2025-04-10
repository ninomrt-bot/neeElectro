import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import os
import datetime

# === IMPORTS PROJET ===
import erp
import opcua_client
# import rfid_reader  # active si tu veux
# import supervision   # active si tu veux

TRANSLATIONS = {
    "fr": {
        "title": "Poste de Pilotage LGN-04",
        "dashboard": "Accueil",
        "of_selection": "Ordres de Fabrication",
        "status": "État des îlots",
        "logs": "Logs",
        "traceability": "Traçabilité",
        "unauthorized": "Veuillez scanner votre badge RFID avant d'accéder à cette section.",
        "export_logs": "Exporter les logs",
        "send_of": "Envoyer l’OF sélectionné",
        "badge_wait": "Veuillez scanner votre badge RFID pour continuer...",
        "badge_ok": "Badge détecté :",
        "badge_info": "Badge accepté",
        "no_of_selected": "Veuillez sélectionner un OF dans la liste.",
        "send_success": "OF {numero} envoyé avec succès.",
        "send_error": "Impossible d’envoyer l’OF.",
        "clear_logs": "🧹 Vider les logs",
        "filter_label": "🔎 Filtrer :",
        "details": "Détails"
    },
    "en": {
        "title": "Production Dashboard LGN-04",
        "dashboard": "Dashboard",
        "of_selection": "Manufacturing Orders",
        "status": "Station Status",
        "logs": "Logs",
        "traceability": "Traceability",
        "unauthorized": "Please scan your RFID badge before accessing this section.",
        "export_logs": "Export logs",
        "send_of": "Send selected MO",
        "badge_wait": "Please scan your RFID badge to continue...",
        "badge_ok": "Badge detected:",
        "badge_info": "Badge accepted",
        "no_of_selected": "Please select an MO from the list.",
        "send_success": "MO {numero} successfully sent.",
        "send_error": "Unable to send the MO.",
        "clear_logs": "🧹 Clear logs",
        "filter_label": "🔎 Filter :",
        "details": "Details"
    }
}

ASSETS = "/home/groupec/Documents/NEE/Assets"

class PilotageApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("1280x720")
        self.title("Pilotage LGN-04")
        self.configure(bg="#10142c")

        self.lang = "fr"
        self.role = "non_identifié"
        self.badge_id = None

        self.logs = []
        self.search_var = tk.StringVar()
        self.traceability_data = []

        # === Logo / Images ===
        self.logo_img = ImageTk.PhotoImage(
            Image.open(os.path.join(ASSETS, "logoENN.PNG")).resize((200, 200))
        )

        # === Topbar ===
        self.topbar = tk.Frame(self, bg="#1b1f3b", height=60)
        self.topbar.pack(side="top", fill="x")

        self.title_label = tk.Label(
            self.topbar,
            text=self.translate("title"),
            font=("Segoe UI", 18, "bold"),
            fg="white",
            bg="#1b1f3b"
        )
        self.title_label.pack(side="left", padx=20)

        self.role_label = tk.Label(
            self.topbar,
            text=f"Rôle : {self.role}",
            font=("Segoe UI", 12),
            bg="#1b1f3b",
            fg="white"
        )
        self.role_label.pack(side="right", padx=10)

        self.flag_frame = tk.Frame(self.topbar, bg="#1b1f3b")
        self.flag_frame.pack(side="right", padx=5)

        # Drapeaux
        flag_fr = Image.open(os.path.join(ASSETS, "autocollant-drapeau-france-rond.jpg")).resize((30, 30))
        flag_uk = Image.open(os.path.join(ASSETS, "sticker-drapeau-anglais-rond.jpg")).resize((30, 30))
        self.flag_fr_img = ImageTk.PhotoImage(flag_fr)
        self.flag_uk_img = ImageTk.PhotoImage(flag_uk)

        tk.Button(self.flag_frame, image=self.flag_fr_img, bd=0, bg="#1b1f3b",
                  command=lambda: self.set_lang("fr")).pack(side="left", padx=2)
        tk.Button(self.flag_frame, image=self.flag_uk_img, bd=0, bg="#1b1f3b",
                  command=lambda: self.set_lang("en")).pack(side="left", padx=2)

        # === Barre latérale ===
        self.sidebar = tk.Frame(self, bg="#16193c", width=200)
        self.sidebar.pack(side="left", fill="y")

        self.content = tk.Frame(self, bg="#202540")
        self.content.pack(side="right", expand=True, fill="both")

        self.nav_buttons = []
        self.frames = {}

        self.add_nav_button("dashboard", self.show_dashboard)
        self.add_nav_button("of_selection", lambda: self.protected_action(self.show_of_selection))
        self.add_nav_button("status", lambda: self.protected_action(self.show_status))
        self.add_nav_button("logs", lambda: self.protected_action(self.show_logs))
        self.add_nav_button("traceability", lambda: self.protected_action(self.show_traceability))

        # Frames internes
        for page_name in ("DashboardPage", "OFPage", "StatusPage", "LogsPage", "TracePage"):
            frame = tk.Frame(self.content, bg="#202540")
            self.frames[page_name] = frame
            frame.place(x=0, y=0, relwidth=1, relheight=1)

        # Logs
        self.tree_logs = None

        # Champ caché pour RFID
        self.hidden_entry = tk.Entry(self)
        self.hidden_entry.place(x=-100, y=-100)
        self.hidden_entry.bind("<Return>", self.on_badge_scan)
        self.hidden_entry.focus()

        # Charger la traçabilité
        self.load_traceability()

        # Page d'accueil
        self.show_dashboard()

    # --------------------------------------------------------------------------
    # TRADUCTION
    # --------------------------------------------------------------------------
    def translate(self, key):
        return TRANSLATIONS[self.lang].get(key, key)

    def set_lang(self, new_lang):
        self.lang = new_lang
        self.title_label.config(text=self.translate("title"))
        for i, text_key in enumerate(["dashboard", "of_selection", "status", "logs", "traceability"]):
            self.nav_buttons[i].config(text=self.translate(text_key))
        self.show_dashboard()

    # --------------------------------------------------------------------------
    # NAVIGATION
    # --------------------------------------------------------------------------
    def add_nav_button(self, key, command):
        btn = tk.Button(
            self.sidebar,
            text=self.translate(key),
            font=("Segoe UI", 13),
            fg="white",
            bg="#16193c",
            activebackground="#3047ff",
            activeforeground="white",
            relief="flat",
            command=command
        )
        btn.pack(fill="x", padx=10, pady=5)
        self.nav_buttons.append(btn)

    def protected_action(self, action):
        if self.role == "non_identifié":
            messagebox.showwarning("Accès refusé", self.translate("unauthorized"))
        else:
            action()

    def show_frame(self, name):
        for f in self.frames.values():
            f.lower()
        self.frames[name].tkraise()

    def clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

    # --------------------------------------------------------------------------
    # BADGE RFID
    # --------------------------------------------------------------------------
    def on_badge_scan(self, event):
        self.badge_id = self.hidden_entry.get().strip()
        self.hidden_entry.delete(0, tk.END)
        self.role = "opérateur"
        self.role_label.config(text=f"Rôle : {self.role}")

        self.ajouter_log(f"Badge {self.badge_id} détecté")
        messagebox.showinfo(self.translate("badge_info"),
                            f"{self.translate('badge_ok')} {self.badge_id}")

    # --------------------------------------------------------------------------
    # TRAÇABILITÉ
    # --------------------------------------------------------------------------
    def load_traceability(self):
        """
        Ex : lire la traçabilité via OPC-UA ou la simuler
        """
        try:
            # Ex : self.traceability_data = opcua_client.lire_traceabilite(erp.get_of_list())
            # On simule :
            self.traceability_data = [
                ("OF123", "En cours", "2025-02-12 08:12"),
                ("OF456", "OK",       "2025-02-12 09:33")
            ]
        except Exception as e:
            self.traceability_data = []
            self.ajouter_log(f"❌ Traçabilité indisponible : {e}")

    def show_traceability(self):
        self.show_frame("TracePage")
        self.clear_frame(self.frames["TracePage"])

        tk.Label(
            self.frames["TracePage"],
            text=self.translate("traceability"),
            fg="white", bg="#202540", font=("Segoe UI", 18, "bold")
        ).pack(pady=10)

        tree = ttk.Treeview(
            self.frames["TracePage"],
            columns=("of", "etat", "horodatage"),
            show="headings",
            height=15
        )
        tree.heading("of", text="OF")
        tree.heading("etat", text="État")
        tree.heading("horodatage", text="Horodatage")
        tree.column("of", width=150)
        tree.column("etat", width=200)
        tree.column("horodatage", width=250)
        tree.pack(padx=20, pady=10)

        for row in self.traceability_data:
            tree.insert("", "end", values=row)

    # --------------------------------------------------------------------------
    # DASHBOARD
    # --------------------------------------------------------------------------
    def show_dashboard(self):
        self.show_frame("DashboardPage")
        self.clear_frame(self.frames["DashboardPage"])

        tk.Label(
            self.frames["DashboardPage"],
            image=self.logo_img,
            bg="#202540"
        ).pack(pady=15)

        tk.Label(
            self.frames["DashboardPage"],
            text=self.translate("title"),
            fg="white", bg="#202540",
            font=("Segoe UI", 20)
        ).pack(pady=10)

        tk.Label(
            self.frames["DashboardPage"],
            text=f"Date : {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}",
            fg="white", bg="#202540",
            font=("Segoe UI", 14)
        ).pack()

        if self.role == "non_identifié":
            tk.Label(
                self.frames["DashboardPage"],
                text=self.translate("badge_wait"),
                fg="lightgray", bg="#202540",
                font=("Segoe UI", 12)
            ).pack(pady=30)

    # --------------------------------------------------------------------------
    # ORDRES DE FABRICATION
    # --------------------------------------------------------------------------
    def show_of_selection(self):
        self.show_frame("OFPage")
        self.clear_frame(self.frames["OFPage"])

        tk.Label(
            self.frames["OFPage"],
            text=self.translate("of_selection"),
            fg="white", bg="#202540",
            font=("Segoe UI", 18, "bold")
        ).pack(pady=10)

        self.tree_of = ttk.Treeview(
            self.frames["OFPage"],
            columns=("Num", "Code", "Qté"),
            show="headings",
            height=15
        )
        self.tree_of.heading("Num", text="Numéro OF")
        self.tree_of.heading("Code", text="Code Produit")
        self.tree_of.heading("Qté", text="Quantité")
        self.tree_of.column("Num", width=150)
        self.tree_of.column("Code", width=400)
        self.tree_of.column("Qté", width=100)
        self.tree_of.pack(padx=10, pady=10)

        self.tree_of.bind("<Double-1>", self.afficher_composants_of)

        # Charger la liste des OF
        try:
            ofs = erp.get_of_list()  # => [{'numero', 'code', 'quantite'}, ...]
            for of_dict in ofs:
                self.tree_of.insert(
                    "",
                    "end",
                    values=(of_dict["numero"], of_dict["code"], of_dict["quantite"])
                )
            self.ajouter_log(f"{len(ofs)} OF chargés depuis Odoo")
        except Exception as e:
            self.ajouter_log(f"❌ Erreur chargement OF : {e}")
            messagebox.showerror("Erreur Odoo", f"Impossible de récupérer les OF.\n{e}")

        # Bouton pour envoyer l'OF à l'automate
        envoyer_btn = tk.Button(
            self.frames["OFPage"],
            text=self.translate("send_of"),
            bg="green", fg="white",
            font=("Segoe UI", 12, "bold"),
            command=self.envoyer_of_selectionne
        )
        envoyer_btn.pack(pady=10)

    def afficher_composants_of(self, event):
        """
        Double-clic sur un OF => On récupère la liste de composants depuis erp.get_of_components()
        """
        selected = self.tree_of.selection()
        if not selected:
            return

        values = self.tree_of.item(selected[0], "values")
        numero, code, quantite = values

        # On veut la liste des composants REELS d'après l'OF => get_of_components()
        composants = erp.get_of_components(numero)  # => ["ModB x3", ...]

        # Fenêtre popup
        popup = tk.Toplevel(self)
        popup.title(f"{self.translate('details')} - {numero}")
        popup.geometry("400x300")
        popup.configure(bg="#202540")

        tk.Label(
            popup,
            text=f"OF : {numero}",
            font=("Arial", 14, "bold"),
            fg="white",
            bg="#202540"
        ).pack(pady=5)

        tk.Label(
            popup,
            text=f"Article : {code}",
            font=("Arial", 12),
            fg="white",
            bg="#202540"
        ).pack(pady=5)

        tk.Label(
            popup,
            text="Composants :",
            font=("Arial", 12, "underline"),
            fg="white",
            bg="#202540"
        ).pack(pady=10)

        for comp in composants:
            tk.Label(
                popup,
                text=comp,
                font=("Arial", 11),
                fg="white",
                bg="#202540"
            ).pack(anchor="w", padx=20)

    def envoyer_of_selectionne(self):
        """
        Envoie l'OF sélectionné à l'automate via OPC-UA
        """
        selected = self.tree_of.selection()
        if not selected:
            messagebox.showwarning("!", self.translate("no_of_selected"))
            return

        values = self.tree_of.item(selected[0], "values")
        of_selectionne = {
            "numero": values[0],
            "code": values[1],
            "quantite": values[2]
        }

        try:
            opcua_client.envoyer_of(of_selectionne)  # Ton code d'envoi
            self.ajouter_log(f"OF {of_selectionne['numero']} envoyé à l’îlot")
            messagebox.showinfo("✅", self.translate("send_success").format(numero=of_selectionne['numero']))
        except Exception as e:
            self.ajouter_log(f"❌ Échec envoi OF {of_selectionne['numero']} : {e}")
            messagebox.showerror("Erreur", self.translate("send_error"))

    # --------------------------------------------------------------------------
    # PAGE STATUS
    # --------------------------------------------------------------------------
    def show_status(self):
        self.show_frame("StatusPage")
        self.clear_frame(self.frames["StatusPage"])

        tk.Label(
            self.frames["StatusPage"],
            text=self.translate("status"),
            fg="white", bg="#202540",
            font=("Segoe UI", 18, "bold")
        ).pack(pady=20)

        for i in range(3):
            tk.Label(
                self.frames["StatusPage"],
                text=f"Îlot LGN-0{i+1} : OK ✅",
                fg="lightgreen", bg="#202540",
                font=("Segoe UI", 14)
            ).pack(pady=5)

    # --------------------------------------------------------------------------
    # PAGE LOGS
    # --------------------------------------------------------------------------
    def show_logs(self):
        self.show_frame("LogsPage")
        self.clear_frame(self.frames["LogsPage"])

        tk.Label(
            self.frames["LogsPage"],
            text=self.translate("logs"),
            fg="white", bg="#202540",
            font=("Segoe UI", 18)
        ).pack(pady=10)

        # Barre de recherche
        search_frame = tk.Frame(self.frames["LogsPage"], bg="#202540")
        search_frame.pack(pady=5)

        tk.Label(
            search_frame,
            text=self.translate("filter_label"),
            fg="white", bg="#202540"
        ).pack(side="left", padx=5)

        search_entry = tk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side="left", padx=5)
        search_entry.bind("<KeyRelease>", self.filtrer_logs)

        tk.Button(
            self.frames["LogsPage"],
            text=self.translate("export_logs"),
            command=self.export_logs
        ).pack(pady=5)
        tk.Button(
            self.frames["LogsPage"],
            text=self.translate("clear_logs"),
            command=self.vider_logs
        ).pack(pady=5)

        self.tree_logs = ttk.Treeview(
            self.frames["LogsPage"],
            columns=("time", "message"),
            show="headings",
            height=20
        )
        self.tree_logs.heading("time", text="Heure")
        self.tree_logs.heading("message", text="Message")
        self.tree_logs.column("time", width=150)
        self.tree_logs.column("message", width=900)
        self.tree_logs.pack(padx=10, pady=10)

        self.filtrer_logs()

    def ajouter_log(self, message):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logs.append((now, message))
        self.filtrer_logs()
        print(f"[LOG] {now} - {message}")

    def filtrer_logs(self, event=None):
        filtre = self.search_var.get().lower()
        if self.tree_logs:
            self.tree_logs.delete(*self.tree_logs.get_children())
            for log in self.logs:
                if filtre in log[0].lower() or filtre in log[1].lower():
                    self.tree_logs.insert("", "end", values=log)

    def vider_logs(self):
        if messagebox.askyesno("Confirmation", "Voulez-vous vraiment vider tous les logs ?"):
            self.logs.clear()
            self.filtrer_logs()
            print("🧹 Logs vidés manuellement.")

    def export_logs(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")]
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("Heure,Message\n")
                for log in self.logs:
                    f.write(f"{log[0]},{log[1]}\n")
            messagebox.showinfo("Export réussi", f"Logs exportés dans :\n{path}")
        except Exception as e:
            messagebox.showerror("Erreur export", f"Impossible d'exporter les logs :\n{e}")

# --------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------
if __name__ == "__main__":
    app = PilotageApp()

    def sauvegarder_logs_automatiquement():
        path = "/home/groupec/Documents/NEE/logs_auto.csv"
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("Heure,Message\n")
                for log in app.logs:
                    f.write(f"{log[0]},{log[1]}\n")
            print(f"✅ Logs automatiquement sauvegardés dans : {path}")
        except Exception as e:
            print(f"❌ Erreur sauvegarde automatique : {e}")

    app.protocol("WM_DELETE_WINDOW", lambda: (sauvegarder_logs_automatiquement(), app.destroy()))
    app.mainloop()
