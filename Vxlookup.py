import socket
import requests
import json
import concurrent.futures
from datetime import datetime
import dns.resolver
import time
from colorama import Fore, Style, init
import random
import sys


init(autoreset=True)
MAX_THREADS = 50

def display_banner():
    """Affiche une bannière stylisée avec le nom du tool"""
    violet = Fore.MAGENTA
    rose = Fore.LIGHTMAGENTA_EX
    reset = Style.RESET_ALL
    
    banner = f"""
{violet}██╗   ██╗██╗  ██╗██╗      ██████╗  ██████╗ ██╗  ██╗██╗   ██╗██████╗
{violet}██║   ██║╚██╗██╔╝██║     ██╔═══██╗██╔═══██╗██║ ██╔╝██║   ██║██╔══██╗
{rose}██║   ██║ ╚███╔╝ ██║     ██║   ██║██║   ██║█████╔╝ ██║   ██║██████╔╝
{rose}╚██╗ ██╔╝ ██╔██╗ ██║     ██║   ██║██║   ██║██╔═██╗ ██║   ██║██╔═══╝
{violet} ╚████╔╝ ██╔╝ ██╗███████╗╚██████╔╝╚██████╔╝██║  ██╗╚██████╔╝██║
{violet}  ╚═══╝  ╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝
{reset}
{violet}  VxLookup v1.0.0| IP/Domaine Intelligence Tool | by Vxpe
{rose}  ----------------------------------------------------------------
{reset}"""
    print(banner)

def get_target():
    """Demande la cible à l'utilisateur avec une petite touche d'humour"""
    jokes = [
        "Entrez une IP ou un domaine (Attention il ne faut pas être trop méchant !)",
        "IP/Domaine à analyser ? (Attention il ne faut pas être trop méchant !)",
        "IP/Domaine à scanner ? (On va trouver quoi Aujourd'hui ?)",
    ]
    
    while True:
        try:
            target = input(f"\n{Fore.LIGHTMAGENTA_EX}[?] {random.choice(jokes)} : {Style.RESET_ALL}").strip()
            if target.lower() in ('exit', 'quit'):
                print(f"{Fore.RED}[!] Bon bah la prochaine fois il ne faudra pas avoir PEUR !\n")
                sys.exit(0)
            if target:
                return target
            print(f"{Fore.YELLOW}[!] T'es sérieux? Tu n'as rien entré!")
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}[!] Interrompu par l'utilisateur mdr !")
            sys.exit(1)

class VxLookup:
    def __init__(self, target: str):
        """Initialise le scanner avec la cible"""
        self.target = target
        self.start_time = time.time()
        self.ip = self._resolve_target()
        self.results = {
            'metadata': {
                'tool': 'VxLookup',
                'version': '2.1.3',
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
    def _resolve_target(self) -> str:
        """Résolution DNS manuelle avec gestion d'erreurs détaillée"""
     
        try:
            socket.inet_aton(self.target)
            print(f"{Fore.LIGHTGREEN_EX}[+] Cible est une IP valide: {self.target}")
            return self.target
        except socket.error:
            pass
        
        
        print(f"{Fore.LIGHTMAGENTA_EX}[*] Résolution DNS pour: {self.target}...")
        try:
            resolved_ip = socket.gethostbyname(self.target)
            print(f"{Fore.LIGHTGREEN_EX}[+] Résolution réussie: {self.target} → {resolved_ip}")
            return resolved_ip
        except socket.gaierror as e:
            print(f"{Fore.RED}[!] Échec de résolution DNS pour {self.target}")
            print(f"{Fore.YELLOW}[*] Détails de l'erreur: {str(e)}")
            
           
            print(f"{Fore.LIGHTMAGENTA_EX}[*] Tentative avec Google DNS (8.8.8.8) comme fallback...")
            try:
                resolver = dns.resolver.Resolver()
                resolver.nameservers = ['8.8.8.8']
                answer = resolver.resolve(self.target, 'A')
                resolved_ip = str(answer[0])
                print(f"{Fore.LIGHTGREEN_EX}[+] Résolution fallback réussie: {resolved_ip}")
                return resolved_ip
            except Exception as fallback_e:
                print(f"{Fore.RED}[!] Échec critique: Impossible de résoudre {self.target}")
                print(f"{Fore.YELLOW}[*] Erreur fallback: {str(fallback_e)}")
                sys.exit(1)

    def scan_ports(self, ports: range = range(1, 1025)) -> dict:
        """Scan de ports avec gestion intelligente des threads"""
        if not hasattr(self, 'ip'):
            print(f"{Fore.RED}[!] Impossible de scanner les ports sans IP valide")
            return {}
            
        print(f"\n{Fore.LIGHTMAGENTA_EX}[*] Lancement du scan de ports sur {self.ip}...")
        print(f"{Fore.CYAN}[*] Configuration: {len(ports)} ports | {MAX_THREADS} threads | timeout 1s")
        
        def _check_port(port):
            """Fonction interne pour vérifier un port"""
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                try:
                    return port if sock.connect_ex((self.ip, port)) == 0 else None
                except Exception as e:
                    print(f"{Fore.YELLOW}[!] Erreur sur le port {port}: {str(e)}")
                    return None
                
        open_ports = []
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
             
                future_to_port = {executor.submit(_check_port, port): port for port in ports}
                for i, future in enumerate(concurrent.futures.as_completed(future_to_port)):
                    port = future_to_port[future]
                    try:
                        result = future.result()
                        if result:
                            open_ports.append(result)
                            print(f"{Fore.LIGHTGREEN_EX}[+] Port {result} ouvert")
                    except Exception as e:
                        print(f"{Fore.YELLOW}[!] Erreur sur le port {port}: {str(e)}")
                    
                  
                    if i % 50 == 0 and i > 0:
                        print(f"{Fore.CYAN}[*] Progression: {i}/{len(ports)} ports testés")
                        
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}[!] Scan interrompu par l'utilisateur")
            print(f"{Fore.YELLOW}[*] Ports ouverts trouvés jusqu'à présent: {open_ports}")
            return open_ports
            
        self.results['ports'] = {
            'open_ports': sorted(open_ports),
            'scan_duration': f"{time.time() - self.start_time:.2f}s"
        }
        return open_ports

    def geo_lookup(self) -> dict:
        """Géolocalisation avec plusieurs fournisseurs et cache"""
        if not hasattr(self, 'ip'):
            return {}
            
        print(f"\n{Fore.LIGHTMAGENTA_EX}[*] Recherche de géolocalisation pour {self.ip}...")
        
      
        providers = [
            {
                'name': "Vxpe's source",
                'url': f"http://ip-api.com/json/{self.ip}?fields=status,message,country,regionName,city,isp,as,query",
                'parser': lambda data: {
                    'IP': data.get('query'),
                    'Ville': data.get('city'),
                    'Région': data.get('regionName'),
                    'Pays': data.get('country'),
                    'Opérateur': data.get('isp'),
                    'ASN': data.get('as'),
                    'Provider': 'Vxpe'
                } if data.get('status') == 'success' else None
            },
            {
                'name': 'Vxpe',
                'url': f"https://ipapi.co/{self.ip}/json/",
                'parser': lambda data: {
                    'IP': self.ip,
                    'Ville': data.get('city'),
                    'Région': data.get('region'),
                    'Pays': data.get('country_name'),
                    'Opérateur': data.get('org'),
                    'ASN': data.get('asn'),
                    'Provider': 'Vxpe'
                }
            }
        ]
        
        geo_data = {}
        for provider in providers:
            try:
                print(f"{Fore.CYAN}[*] Essai avec {provider['name']}...")
                response = requests.get(provider['url'], timeout=5, headers={
                    'User-Agent': 'Mozilla/5.0 (VxLookup/2.1.3; +https://github.com/SecureVxpe/VxLookup)'
                })
                data = response.json()
                
                if parsed := provider['parser'](data):
                    geo_data = parsed
                    print(f"{Fore.LIGHTGREEN_EX}[+] Données trouvées via {provider['name']}")
                    break
                    
            except Exception as e:
                print(f"{Fore.YELLOW}[!] Erreur avec {provider['name']}: {str(e)}")
                continue
                
        if not geo_data:
            geo_data = {k: "N/A" for k in ['IP', 'Ville', 'Région', 'Pays', 'Opérateur', 'ASN']}
            geo_data['Erreur'] = "Tous les providers ont échoué"
            print(f"{Fore.RED}[!] Impossible d'obtenir des données de géolocalisation")
            
        self.results['geo'] = geo_data
        return geo_data

    def dns_lookup(self) -> dict:
        """Recherche DNS avancée avec détection des erreurs"""
        if '.' not in self.target or self.target.replace('.', '').isdigit():
            print(f"{Fore.YELLOW}[!] La cible est une IP, recherche DNS ignorée")
            self.results['dns'] = {'info': 'DNS lookup skipped for IP address'}
            return {}
            
        print(f"\n{Fore.LIGHTMAGENTA_EX}[*] Recherche DNS pour {self.target}...")
        
        records = {}
        types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA']
        
        for type_ in types:
            try:
                answers = dns.resolver.resolve(self.target, type_)
                records[type_] = [r.to_text() for r in answers]
                print(f"{Fore.LIGHTGREEN_EX}[+] {type_}: {', '.join(records[type_])}")
                
              
                if random.random() < 0.3:
                    time.sleep(0.1 + random.random() * 0.5)
                    
            except dns.resolver.NoAnswer:
                records[type_] = []
            except dns.resolver.NXDOMAIN:
                print(f"{Fore.RED}[-] Le domaine {self.target} n'existe pas")
                records[type_] = ["NXDOMAIN"]
                break
            except dns.resolver.Timeout:
                print(f"{Fore.YELLOW}[-] Timeout pour {type_}")
                records[type_] = ["Timeout"]
            except Exception as e:
                print(f"{Fore.YELLOW}[-] Erreur {type_}: {str(e)}")
                records[type_] = [f"Error: {str(e)}"]
                
        self.results['dns'] = records
        return records

    def run_full_scan(self):
        """Exécute toutes les analyses avec des messages de statut"""
        print(f"\n{Fore.MAGENTA}=== Début de l'analyse pour {self.target} ==={Style.RESET_ALL}")
        
        
        geo_data = self.geo_lookup()
        print(f"\n{Fore.CYAN}=== Géolocalisation ===")
        for k, v in geo_data.items():
            if k not in ('Erreur', 'Provider'):
                print(f"{Fore.LIGHTBLUE_EX}{k:>10}: {Style.RESET_ALL}{v or 'N/A'}")
        if 'Provider' in geo_data:
            print(f"{Fore.LIGHTBLUE_EX}{'Source':>10}: {Style.RESET_ALL}{geo_data['Provider']}")
        
       
        self.scan_ports()
        
        
        if '.' in self.target and not self.target.replace('.', '').isdigit():
            self.dns_lookup()
        
    
        duration = time.time() - self.start_time
        print(f"\n{Fore.MAGENTA}=== Résumé de l'analyse ===")
        print(f"{Fore.LIGHTBLUE_EX}Target: {Style.RESET_ALL}{self.target}")
        print(f"{Fore.LIGHTBLUE_EX}IP: {Style.RESET_ALL}{self.ip}")
        print(f"{Fore.LIGHTBLUE_EX}Durée: {Style.RESET_ALL}{duration:.2f} secondes")
        print(f"{Fore.MAGENTA}========================={Style.RESET_ALL}")

def main():
    """Point d'entrée principal avec gestion des erreurs"""
    try:
        display_banner()
        target = get_target()
        
        scanner = VxLookup(target)
        scanner.run_full_scan()
        
  
        save = input(f"\n{Fore.LIGHTMAGENTA_EX}[?] Sauvegarder les résultats? (o/N): {Style.RESET_ALL}").lower()
        if save == 'o':
            filename = f"vxlookup_{target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(scanner.results, f, indent=4, ensure_ascii=False)
                print(f"{Fore.LIGHTGREEN_EX}[+] Résultats sauvegardés dans {filename}")
            except Exception as e:
                print(f"{Fore.RED}[!] Erreur lors de la sauvegarde: {str(e)}")
                
        print(f"\n{Fore.MAGENTA}[*] Fin de VxLookup. Merci À bientôt ! ){Style.RESET_ALL}")
        
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[!] Interrompu par l'utilisateur (trop pressé?)")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}[!] Erreur ?: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()