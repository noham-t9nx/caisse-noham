	
to nononite09
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import urllib.request
import base64
import cv2
import numpy as np
import serial
import time
import json
import os

# Configuration de la caméra
url = "http://192.168.1.4/video/mjpg.cgi"
username = "admin"
password = "azerty12345"
credentials = f"{username}:{password}"
encoded_credentials = base64.b64encode(credentials.encode('ascii'))
request = urllib.request.Request(url)
request.add_header('Authorization', 'Basic %s' % encoded_credentials.decode("ascii"))
stream = urllib.request.urlopen(request)
bytes_data = b''

PORT_CLIENT = '/dev/ttyS5'
BAUDRATE = 9600
FICHIER_CLIENTS = "/home/caisse01/caisse_yuno/clients.json"
FICHIER_BOISSONS = "/home/caisse01/caisse_yuno/produits_boissons.json"
FICHIER_SUCRERIES = "/home/caisse01/caisse_yuno/produits_sucreries.json"

root = tk.Tk()
root.title("Caisse avec Caméra")
root.geometry("900x700")

# Fenêtre caméra en bas à gauche
frame_camera = tk.Frame(root)
frame_camera.place(x=10, y=50, width=300, height=180)
label_video = tk.Label(frame_camera)
label_video.pack()

produits_boissons = {}
produits_sucreries = {}
ticket = []
frame_boissons = None
frame_sucreries = None
listebox = None
label_total = None

def afficher_image():
    global bytes_data
    try:
        bytes_data += stream.read(1024)
        a = bytes_data.find(b'\xff\xd8')
        b = bytes_data.find(b'\xff\xd9')
        if a != -1 and b != -1:
            jpg = bytes_data[a:b+2]
            bytes_data = bytes_data[b+2:]
            image = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image_pil = Image.fromarray(image)
            image_pil = image_pil.resize((320, 180))
            image_tk = ImageTk.PhotoImage(image_pil)
            label_video.config(image=image_tk)
            label_video.image = image_tk
    except Exception as e:
        print("Erreur caméra:", e)
    root.after(15, afficher_image)

def sauvegarder_produits():
    with open(FICHIER_BOISSONS, "w") as f:
        json.dump(produits_boissons, f, indent=4)
    with open(FICHIER_SUCRERIES, "w") as f:
        json.dump(produits_sucreries, f, indent=4)

def charger_produits():
    global produits_boissons, produits_sucreries
    if os.path.exists(FICHIER_BOISSONS):
        with open(FICHIER_BOISSONS, "r") as f:
            produits_boissons = json.load(f)
    if os.path.exists(FICHIER_SUCRERIES):
        with open(FICHIER_SUCRERIES, "r") as f:
            produits_sucreries = json.load(f)

def charger_clients():
    if os.path.exists(FICHIER_CLIENTS):
        with open(FICHIER_CLIENTS, "r") as f:
            return json.load(f)
    return {}

def sauvegarder_clients(donnees):
    with open(FICHIER_CLIENTS, "w") as f:
        json.dump(donnees, f, indent=4)

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

def afficher_interface_admin():
    fen = tk.Toplevel()
    fen.title("Mode Administrateur")

    choix_categorie = tk.StringVar(value="boisson")
    tk.Radiobutton(fen, text="Boisson", variable=choix_categorie, value="boisson").pack()
    tk.Radiobutton(fen, text="Sucrerie", variable=choix_categorie, value="sucrerie").pack()

    tk.Label(fen, text="Nom du produit :").pack()
    nom_entry = tk.Entry(fen)
    nom_entry.pack()

    def ajouter_ou_modifier():
        nom = nom_entry.get()
        if not nom:
            messagebox.showerror("Erreur", "Nom vide")
            return
        if choix_categorie.get() == "boisson":
            prix_250 = simpledialog.askfloat("Prix", "Prix pour 250mL")
            prix_330 = simpledialog.askfloat("Prix", "Prix pour 330mL")
            prix_500 = simpledialog.askfloat("Prix", "Prix pour 500mL")
            produits_boissons[nom] = {
                "250mL": prix_250,
                "330mL": prix_330,
                "500mL": prix_500
            }
        else:
            prix_unite = simpledialog.askfloat("Prix", "Prix pour 1 paquet")
            produits_sucreries[nom] = {"1 paquet": prix_unite}
        sauvegarder_produits()
        messagebox.showinfo("Succès", "Produit ajouté/modifié")
        afficher_catalogue()

    def supprimer():
        nom = nom_entry.get()
        dico = produits_boissons if choix_categorie.get() == "boisson" else produits_sucreries
        if nom in dico:
            del dico[nom]
            sauvegarder_produits()
            messagebox.showinfo("Succès", "Produit supprimé")
            afficher_catalogue()
        else:
            messagebox.showerror("Erreur", "Produit introuvable")

    tk.Button(fen, text="Ajouter / Modifier", command=ajouter_ou_modifier).pack(pady=5)
    tk.Button(fen, text="Supprimer", command=supprimer).pack(pady=5)

def demander_code_admin():
    code = simpledialog.askstring("Code administrateur", "Entrer le code :", show='*')
    if code == "1234":
        afficher_interface_admin()
    else:
        messagebox.showerror("Erreur", "Code incorrect")

def ajouter_article(nom_produit, dico):
    if dico == produits_boissons:
        popup = tk.Toplevel()
        popup.title("Choisir le format")
        def choix_format(fmt):
            prix = dico[nom_produit][fmt]
            ligne = f"{nom_produit} ({fmt}) - {prix:.2f} €"
            ticket.append((nom_produit, fmt, prix))
            listebox.insert(tk.END, ligne)
            totaliser()
            popup.destroy()
        for fmt in ["250mL", "330mL", "500mL"]:
            if fmt in dico[nom_produit]:
                tk.Button(popup, text=fmt, command=lambda f=fmt: choix_format(f)).pack(pady=5)
    else:
        choix = simpledialog.askstring("Quantité", "Combien en voulez-vous ?")
        try:
            quantite = int(choix)
        except:
            messagebox.showerror("Erreur", "Nombre invalide")
            return
        for format_, prix in dico[nom_produit].items():
            ligne = f"{nom_produit} ({format_}) x{quantite} - {prix * quantite:.2f} €"
            ticket.append((nom_produit, format_, prix * quantite))
            listebox.insert(tk.END, ligne)
        totaliser()

def totaliser():
    total = sum(p[2] for p in ticket)
    label_total.config(text=f"Total : {total:.2f} €")

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

def abandonner():
    if messagebox.askyesno("Annuler", "Voulez-vous vraiment annuler la commande ?"):
        ticket.clear()
        listebox.delete(0, tk.END)
        totaliser()
       
def afficher_catalogue():
    global frame_boissons, frame_sucreries, listebox, label_total
    root.title("Caisse - Boissons et Snacks")
    for widget in root.winfo_children():
        if isinstance(widget, tk.Button) and widget["text"] not in ["Mode administrateur", "Avez-vous un compte client ?"]:
            widget.destroy()

    tk.Button(root, text="Avez-vous un compte client ?", bg="lightblue", command=afficher_choix_client).place(x=10, y=10)

    bouton_admin = tk.Button(root, text="Mode administrateur", bg="orange", command=demander_code_admin)
    bouton_admin.place(x=850, y=10)

    frame_produits = tk.Frame(root)
    frame_produits.place(x=350, y=50)

    if frame_boissons:
        frame_boissons.destroy()
    if frame_sucreries:
        frame_sucreries.destroy()

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

    listebox = tk.Listbox(root, width=50)
    listebox.place(x=350, y=450)

    label_total = tk.Label(root, text="Total : 0.00 €", font=("Arial", 14, "bold"))
    label_total.place(x=350, y=620)

    tk.Button(root, text="Encaisser la commande", bg="green", fg="white", font=("Arial", 11, "bold"),
              command=encaisser).place(x=350, y=650)
    tk.Button(root, text="Abandonner la commande", bg="red", fg="white", font=("Arial", 11, "bold"),
              command=abandonner).place(x=542, y=650)

    image_shop = Image.open("/home/caisse01/Téléchargements/shop.png").resize((160, 160))
    photo_shop = ImageTk.PhotoImage(image_shop)
    label_shop = tk.Label(root, image=photo_shop)
    label_shop.image = photo_shop
    label_shop.place(x=845, y=220)

    image_lycee = Image.open("/home/caisse01/Téléchargements/Saint-Vinc.png").resize((160, 160))
    photo_lycee = ImageTk.PhotoImage(image_lycee)
    label_lycee = tk.Label(root, image=photo_lycee)
    label_lycee.image = photo_lycee
    label_lycee.place(x=845, y=50)
   
    image_lycee = Image.open("/home/caisse01/Téléchargements/promo.png").resize((300, 180))
    photo_lycee = ImageTk.PhotoImage(image_lycee)
    label_lycee = tk.Label(root, image=photo_lycee)
    label_lycee.image = photo_lycee
    label_lycee.place(x=10, y=250)

if __name__ == "__main__":
    charger_produits()
    afficher_image()
    afficher_catalogue()
    root.mainloop()
