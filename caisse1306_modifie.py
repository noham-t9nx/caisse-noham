#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox, simpledialog
import serial
import time
import json
import os

PORT_CLIENT = '/dev/ttyS5'
BAUDRATE = 9600
FICHIER_CLIENTS = "/home/caisse01/caisse_yuno/clients.json"

root = tk.Tk()
root.withdraw()

def charger_clients():
    if os.path.exists(FICHIER_CLIENTS):
        with open(FICHIER_CLIENTS, "r") as f:
            return json.load(f)
    return {}

def sauvegarder_clients(donnees):
    with open(FICHIER_CLIENTS, "w") as f:
        json.dump(donnees, f, indent=4)

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

def afficher_choix_client():
    fen = tk.Toplevel()
    fen.title("Compte client")
    tk.Label(fen, text="Choisissez une option :", font=("Arial", 12)).pack(pady=10)
    tk.Button(fen, text="Oui, se connecter", command=lambda: (fen.destroy(), fenetre_connexion())).pack(pady=5)
    tk.Button(fen, text="Non, créer un compte", command=lambda: (fen.destroy(), fenetre_creation_compte())).pack(pady=5)

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
        email = email_entry.get()
        mdp = password_entry.get()
        clients = charger_clients()
        if email in clients and clients[email]["mot_de_passe"] == mdp:
            messagebox.showinfo("Succès", f"Bienvenue {clients[email]['prenom']} !")
            fen.destroy()
        else:
            messagebox.showerror("Erreur", "Email ou mot de passe incorrect")

    tk.Button(fen, text="Se connecter", command=valider_connexion).pack(pady=10)

def fenetre_creation_compte():
    fen = tk.Toplevel()
    fen.title("Créer un compte")

    champs = ["Prénom", "Nom", "Email", "Mot de passe", "Confirmer mot de passe"]
    entrees = {}

    for champ in champs:
        tk.Label(fen, text=champ).pack()
        entrees[champ] = tk.Entry(fen, show="*" if "mot de passe" in champ.lower() else None)
        entrees[champ].pack()

    def valider_creation():
        valeurs = {champ: entrees[champ].get() for champ in champs}
        if not all(valeurs.values()):
            messagebox.showerror("Erreur", "Tous les champs doivent être remplis.")
            return
        if valeurs["Mot de passe"] != valeurs["Confirmer mot de passe"]:
            messagebox.showerror("Erreur", "Les mots de passe ne correspondent pas.")
            return
        clients = charger_clients()
        email = valeurs["Email"]
        if email in clients:
            messagebox.showerror("Erreur", "Ce compte existe déjà.")
            return
        clients[email] = {
            "prenom": valeurs["Prénom"],
            "nom": valeurs["Nom"],
            "mot_de_passe": valeurs["Mot de passe"]
        }
        sauvegarder_clients(clients)
        messagebox.showinfo("Succès", "Compte créé avec succès !")
        fen.destroy()

    tk.Button(fen, text="Créer le compte", command=valider_creation).pack(pady=10)

def afficher_catalogue():
    root.deiconify()
    root.title("Caisse - Boissons et Snacks")
    root.geometry("500x600")

    bouton_compte = tk.Button(root, text="Avez-vous un compte client ?", bg="lightblue", command=afficher_choix_client)
    bouton_compte.place(x=10, y=10)

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
    afficher_catalogue()
    root.mainloop()
