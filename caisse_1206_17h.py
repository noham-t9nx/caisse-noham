import tkinter as tk
from tkinter import messagebox, simpledialog
import serial
import time

PORT_CLIENT = '/dev/ttyS5'
BAUDRATE = 9600

root = tk.Tk()
root.withdraw()  # Masquer la fenêtre principale au démarrage

def fenetre_plein_ecran(fen):
    fen.attributes('-fullscreen', True)
    fen.bind('<Escape>', lambda e: fen.attributes('-fullscreen', False))

def afficher_client_serie(total):
    try:
        with serial.Serial(PORT_CLIENT, BAUDRATE, timeout=1) as client:
            time.sleep(0.3)
            client.write(b'\x0C')
            lignes = [
                "Total a payer :",
                f"{total:.2f} EUR",
                "Merci !"
            ]
            for ligne in lignes:
                client.write((ligne + '\r\n').encode('utf-8'))
    except Exception as e:
        print("Erreur série client :", e)

def afficher_bienvenue_client():
    try:
        with serial.Serial(PORT_CLIENT, BAUDRATE, timeout=1) as client:
            time.sleep(0.3)
            client.write(b'\x0C')
            client.write(b"Bienvenue !\r\nCommande en cours...\r\n")
    except Exception as e:
        print("Erreur affichage bienvenue :", e)

def afficher_page_connexion():
    choix_fenetre = tk.Toplevel()
    choix_fenetre.title("Connexion Client")
    tk.Label(choix_fenetre, text="Avez-vous un compte client ?", font=("Arial", 14)).pack(pady=20)

    def se_connecter():
        choix_fenetre.destroy()
        fenetre_connexion()

    def creer_compte():
        choix_fenetre.destroy()
        fenetre_creation_compte()

    def continuer_sans_compte():
        choix_fenetre.destroy()
        afficher_catalogue()

    tk.Button(choix_fenetre, text="Oui, se connecter", command=se_connecter, width=25).pack(pady=5)
    tk.Button(choix_fenetre, text="Non, je souhaite créer un compte", command=creer_compte, width=25).pack(pady=5)
    tk.Button(choix_fenetre, text="Non, continuer sans compte", command=continuer_sans_compte, width=25).pack(pady=5)

def fenetre_connexion():
    fen = tk.Toplevel()
    fen.title("Connexion")
    tk.Label(fen, text="Email:").pack()
    email_entry = tk.Entry(fen)
    email_entry.pack()

    tk.Label(fen, text="Mot de passe:").pack()
    password_entry = tk.Entry(fen, show="*")
    password_entry.pack()

    def valider_connexion():
        if email_entry.get() and password_entry.get():
            fen.destroy()
            afficher_catalogue()
        else:
            messagebox.showerror("Erreur", "Veuillez entrer vos informations")

    tk.Button(fen, text="Se connecter", command=valider_connexion).pack(pady=10)

def fenetre_creation_compte():
    fen = tk.Toplevel()
    fen.title("Créer un compte")
    champs = ["Prénom", "Nom", "Email", "Téléphone", "Code postal", "Mot de passe", "Confirmer mot de passe"]
    entrees = {}
    for champ in champs:
        tk.Label(fen, text=champ).pack()
        entrees[champ] = tk.Entry(fen, show="*" if "mot de passe" in champ.lower() else None)
        entrees[champ].pack()

    def valider_creation():
        valeurs = {champ: entree.get() for champ, entree in entrees.items()}
        if not all(valeurs.values()):
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs")
            return
        if valeurs["Mot de passe"] != valeurs["Confirmer mot de passe"]:
            messagebox.showerror("Erreur", "Les mots de passe ne correspondent pas")
            return
        fen.destroy()
        afficher_catalogue()

    tk.Button(fen, text="Créer mon compte", command=valider_creation).pack(pady=10)

def afficher_catalogue():
    root.deiconify()  # Réaffiche la fenêtre principale
    root.title("Caisse - Boissons et Snacks")
    root.geometry("500x600")

    frame_produits = tk.Frame(root)
    frame_produits.pack(pady=10)

    frame_boissons = tk.Frame(frame_produits)
    frame_sucreries = tk.Frame(frame_produits)
    frame_boissons.grid(row=0, column=0, padx=10)
    frame_sucreries.grid(row=0, column=1, padx=10)

    for produit in produits_boissons:
        tk.Button(frame_boissons, text=produit, width=20, height=2,
                  command=lambda p=produit: ajouter_article(p, produits_boissons)).pack(pady=4)

    for snack in produits_sucreries:
        tk.Button(frame_sucreries, text=snack, width=20, height=2,
                  command=lambda s=snack: ajouter_article(s, produits_sucreries)).pack(pady=4)

    global listebox, label_total
    listebox = tk.Listbox(root, width=50)
    listebox.pack(pady=10)

    label_total = tk.Label(root, text="Total : 0.00 €", font=("Arial", 14, "bold"))
    label_total.pack(pady=5)

    tk.Button(root, text="Encaisser la commande", bg="green", fg="white", font=("Arial", 12, "bold"),
              command=encaisser).pack(pady=5)

    tk.Button(root, text="Abandonner la commande", bg="red", fg="white", font=("Arial", 12, "bold"),
              command=reinitialiser_client).pack(pady=10)

    afficher_bienvenue_client()

def ajouter_article(nom_produit, dico_produit):
    def choix_taille(taille):
        prix = dico_produit[nom_produit][taille]
        ligne = f"{nom_produit} ({taille}) - {prix:.2f} €"
        ticket.append((nom_produit, taille, prix))
        listebox.insert(tk.END, ligne)
        totaliser()
        popup.destroy()

    popup = tk.Toplevel()
    popup.title(f"{nom_produit} - Choisir le format")
    for taille in dico_produit[nom_produit]:
        tk.Button(popup, text=taille, width=15, command=lambda t=taille: choix_taille(t)).pack(pady=5)

def totaliser():
    total = sum(p[2] for p in ticket)
    label_total.config(text=f"Total : {total:.2f} €")
    afficher_client_serie(total)

def encaisser():
    if not ticket:
        messagebox.showinfo("Information", "Aucun article")
        return
    total = sum(p[2] for p in ticket)

    def payer_en_especes():
        montant_str = simpledialog.askstring("Paiement", f"Total à payer : {total:.2f} €\nMontant donné par le client (€) :")
        if montant_str is None:
            return
        try:
            montant_donne = float(montant_str)
            rendu = montant_donne - total
            if rendu < 0:
                messagebox.showwarning("Montant insuffisant", f"Le client doit encore : {abs(rendu):.2f} €")
            else:
                messagebox.showinfo("Rendu de monnaie", f"À rendre au client : {rendu:.2f} €")
                finaliser_commande()
        except ValueError:
            messagebox.showerror("Erreur", "Montant invalide")

    def cb_contact():
        messagebox.showinfo("Paiement CB", "Veuillez insérer la carte...")
        time.sleep(0.5)
        code = simpledialog.askstring("Code PIN", "Entrer le code à 4 chiffres :", show='*')
        if code and len(code) == 4 and code.isdigit():
            messagebox.showinfo("Paiement CB", "Paiement accepté.\nMerci.")
            finaliser_commande()
        else:
            messagebox.showerror("Erreur", "Code invalide ou annulé")

    def cb_sans_contact():
        messagebox.showinfo("Paiement CB", "Veuillez approcher la carte sans contact...")
        time.sleep(2)
        messagebox.showinfo("Paiement CB", "Paiement sans contact accepté.\nMerci.")
        finaliser_commande()

    def choisir_type_cb():
        cb_popup = tk.Toplevel()
        cb_popup.title("Choisir le type de CB")
        tk.Label(cb_popup, text="Paiement CB :").pack(pady=10)
        tk.Button(cb_popup, text="Sans contact", command=lambda: (cb_popup.destroy(), cb_sans_contact())).pack(pady=5)
        tk.Button(cb_popup, text="Avec code (contact)", command=lambda: (cb_popup.destroy(), cb_contact())).pack(pady=5)

    def finaliser_commande():
        ticket.clear()
        listebox.delete(0, tk.END)
        totaliser()

    popup = tk.Toplevel()
    popup.title("Mode de paiement")
    tk.Label(popup, text="Choisir le mode de paiement :").pack(pady=10)
    tk.Button(popup, text="Espèces", width=20, command=lambda: (popup.destroy(), payer_en_especes())).pack(pady=5)
    tk.Button(popup, text="Carte bancaire", width=20, command=lambda: (popup.destroy(), choisir_type_cb())).pack(pady=5)

def reinitialiser_client():
    ticket.clear()
    listebox.delete(0, tk.END)
    label_total.config(text="Total : 0.00 €")
    afficher_bienvenue_client()

produits_boissons = {
    "Café": {"150mL": 1.00, "330mL": 1.30, "500mL": 1.50},
    "Thé": {"150mL": 1.10, "330mL": 1.40, "500mL": 1.60},
    "Chocolat chaud": {"150mL": 1.30, "330mL": 1.60, "500mL": 1.90},
    "Lait chaud": {"150mL": 0.90, "330mL": 1.20, "500mL": 1.40},
    "Fanta": {"150mL": 1.20, "330mL": 1.50, "500mL": 1.80},
    "Coca-Cola": {"150mL": 1.00, "330mL": 1.20, "500mL": 1.50}
}

produits_sucreries = {
    "Twix": {"1 paquet": 0.80, "2 paquets": 1.40},
    "Oreo": {"1 paquet": 0.90, "2 paquets": 1.60},
    "Kinder": {"1 paquet": 1.20, "2 paquets": 2.00},
    "Chips": {"un sachet": 1.50, "2 sachets": 2.50},
    "Milka": {"une tablette": 2.00, "2 tablettes": 3.50},
    "Bounty": {"1 paquet": 1.00, "2 paquets": 1.80}
}

ticket = []

if __name__ == "__main__":
    afficher_page_connexion()
    root.mainloop()
