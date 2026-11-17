"""Everyday consumer technology knowledge: keyword-matched short answers.

Rule syntax: groups separated by '&'; each group lists alternatives separated by '|'.
A rule matches when every group has at least one alternative present (after light stemming).
More groups means a more specific rule, and the most specific match wins.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Optional

from ..arbiter import Proposal

if TYPE_CHECKING:  # pragma: no cover
    from ..engine import Context


def _stem(w: str) -> str:
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 5 and w.endswith("ing"):
        return w[:-3]
    if len(w) > 4 and w.endswith("ed"):
        return w[:-2]
    if len(w) > 4 and w.endswith(("ses", "xes", "zes", "ches", "shes")):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


RULES = [
    # ---- passwords and accounts ----
    ("password & strong|good|secure|safe|create|make|choose|pick|best|tip|long",
     "A strong password is long, ideally several random words or characters, and different for every account. A password manager can create and remember them for you."),
    ("password & manager|vault",
     "A password manager is an app that creates, stores and fills in strong unique passwords for you, so you only need to remember one main password."),
    ("password & reuse|same|share|everywhere",
     "Reusing the same password is risky, because if one site is breached attackers can try it on your other accounts. Use a different password for each account."),
    ("password & forgot|forget|reset|recover|lost|lose",
     "If you forgot your password, use the forgot password link on the sign in page to reset it through your email or phone. Choose a new, unique password afterwards."),
    ("password & often|change|rotate|how long",
     "You should change a password if you think it was exposed or the service was breached, rather than on a fixed schedule. A long unique password is more important than changing it often."),
    ("password & hack|crack|guess|leak|breach|stolen",
     "Passwords get cracked by guessing, reuse after breaches and phishing. Long, unique passwords and two factor authentication make that much harder."),
    ("password & write|store|save|remember|keep",
     "The safest place to keep passwords is a reputable password manager. Saving them in an unprotected note or reusing easy ones is risky."),
    ("passphrase", "A passphrase is a password made of several random words, which is long and easier to remember than random characters."),
    ("two|2|multi & factor|step & authentication|verification|auth|2fa",
     "Two factor authentication asks for a second proof of identity, such as a code on your phone, as well as your password, so a stolen password alone is not enough."),
    ("2fa|mfa", "Two factor authentication asks for a second proof of identity, such as a code from an app or your phone, on top of your password."),
    ("authenticator & app", "An authenticator app generates short time limited codes on your phone that you enter as a second step when you sign in."),
    ("biometric|fingerprint|face & unlock|id|recognition|login|sign",
     "Biometric login uses your fingerprint or face to unlock a device. It is convenient, and you should keep a strong passcode as a backup."),
    ("account & hacked|compromised|stolen|hijack|breach|taken",
     "If your account was hacked, change its password right away, turn on two factor authentication, log out other devices and check your recovery email and phone for changes."),
    ("account & secure|protect|safe|safer",
     "To secure an account, use a strong unique password, turn on two factor authentication, keep recovery details current and watch for phishing messages."),
    ("passkey", "A passkey is a password replacement that lets you sign in with your device unlock, such as a fingerprint, face or PIN, and cannot be phished like a password."),
    ("sso|single & sign", "Single sign on lets you use one trusted account to log in to several services, so you manage fewer passwords."),
    ("captcha", "A CAPTCHA is a small test that helps websites tell real people from automated bots."),
    ("pin & code|number & phone|device",
     "Use a PIN or passcode that is hard to guess, not birthdays or repeating digits, and set one on every phone and tablet."),
    # ---- security and malware ----
    ("phishing", "Phishing is when scammers pretend to be a trusted company or person to trick you into giving passwords or money. Do not click suspicious links, and go to the official site yourself instead."),
    ("scam|fake|suspicious|spot|recognize|identify & email|message|text|sms|link",
     "Be wary of messages that create urgency, ask for passwords or payments, or contain odd links or sender addresses. Do not click, and contact the company through its official website."),
    ("spam & email|mail|message|text|call",
     "Spam is unwanted bulk messages. Do not reply or click links in it, mark it as spam in your email app, and use the built in filters."),
    ("email & attachment|attach",
     "Be careful opening email attachments from unknown senders, since they can hide malware. If you did not expect it, check with the sender another way first."),
    ("virus|malware", "Malware is harmful software such as viruses and spyware. Keep your system and apps updated, only install software from trusted sources and run a security scan if you suspect an infection."),
    ("ransomware", "Ransomware is malware that locks your files and demands payment. Keep offline backups and updated software, and avoid opening unknown attachments."),
    ("spyware|stalkerware|keylogger", "Spyware is software that secretly watches what you do. Keep your device updated, remove unknown apps, and run a security scan if you suspect it."),
    ("antivirus", "Antivirus software scans for and removes malware. Built in protection on modern systems is a good start, and you should keep it updated and avoid unsafe downloads."),
    ("firewall", "A firewall is a barrier that filters network traffic and blocks unwanted connections to or from your device."),
    ("vpn", "A VPN creates an encrypted connection between your device and a server, which hides your traffic from the local network, for example on public Wi-Fi. It does not make you fully anonymous."),
    ("encryption|encrypt|encrypted", "Encryption scrambles data so only someone with the right key can read it, which protects information stored on a device or sent over the internet."),
    ("https|padlock|lock & icon|site|website|secure", "HTTPS means the connection between your browser and the website is encrypted. It does not guarantee the site itself is trustworthy."),
    ("public & wifi|wi-fi|hotspot|network",
     "Public Wi-Fi can be risky because others on the network may snoop. Avoid sensitive logins on it, stick to HTTPS sites, or use a VPN."),
    ("hacker|hacking|hacked & what|who", "A hacker is someone who gets into computers or networks, sometimes to cause harm and sometimes to find and fix security weaknesses."),
    ("data & breach|leak", "A data breach is when private information is exposed or stolen from a company. If you are affected, change your passwords and watch your accounts for unusual activity."),
    ("social & engineering", "Social engineering is tricking people rather than machines into giving up information or access, often by pretending to be someone trusted."),
    ("identity & theft|stolen", "Identity theft is when someone uses your personal details without permission. Protect it with strong passwords, careful sharing and checking your accounts regularly."),
    ("safe|secure|protect & online|internet|browse|browsing|surf|digital",
     "To stay safe online, use strong unique passwords, turn on two factor authentication, keep software updated, and be careful with links, attachments and what you share."),
    ("software & download|install & safe|trusted|official|where|source",
     "Download software only from official websites and app stores, and avoid cracked or pirated versions, which often contain malware."),
    ("pop & up|popups|ads", "Pop up warnings that say your device is infected are usually scams. Close the tab without clicking, and do not call numbers shown in them."),
    ("lost|stolen|missing|find & phone|laptop|device|tablet",
     "If your device is lost or stolen, use its find my device feature to locate, lock or erase it, change your important passwords and contact your carrier."),
    ("unknown|unfamiliar|random & usb|drive|stick|charger|cable",
     "Do not plug in unknown USB drives or use untrusted charging ports, since they can carry malware or steal data."),
    ("qr & code", "A QR code is a square barcode your camera can scan to open a link. Check the address before you open it, because a QR code can lead to a fake site."),
    ("cookie", "Cookies are small files websites store in your browser to remember things like logins and preferences. You can clear them or block them in your browser settings."),
    ("privacy & protect|improve|better|keep|settings",
     "To protect your privacy, review app permissions, limit what you share on social media, use strong passwords and turn on privacy settings in your accounts and browser."),
    ("permission & app", "App permissions control what an app can access, like your camera, location or contacts. Only allow what the app really needs and review them in your settings."),
    ("location & tracking|track|share|turn|off", "You can limit location tracking in your device settings by turning off location services or allowing it only while an app is in use."),
    ("tracking|tracker|track & online|ads|website", "Websites track you with cookies and similar tools. You can limit this with browser privacy settings, tracker blocking and clearing cookies."),
    ("incognito|private & browsing|mode|window", "Private browsing does not save your history or cookies on that device, but it does not hide your activity from websites, your network or your internet provider."),
    ("clear|delete & history|cache|cookie & browser",
     "You can clear your browser history, cache and cookies from the browser settings under privacy or history. This can free space and fix some loading problems."),
    ("cache", "A cache is stored temporary data that helps apps and websites load faster. Clearing it can fix glitches and free some space."),
    ("deepfake", "A deepfake is fake audio, images or video made with AI to look real. Check the source before trusting or sharing surprising media."),
    ("social & media & privacy|safe|settings", "On social media, review who can see your posts, limit personal details like your address, and use two factor authentication."),
    # ---- updates and backups ----
    ("update|updates & software|system|security|device|phone|computer|app|windows|ios|android|install|patch",
     "You should install updates because they fix security holes and bugs and often add features. Keeping software updated is one of the best ways to stay safe."),
    ("update & software|system|device|phone|computer|windows|ios|android",
     "To update, open your device settings, look for software or system update, and install what is offered. Keep the device plugged in and connected to Wi-Fi while it installs."),
    ("update & stuck|fail|failed|freeze|frozen",
     "If an update is stuck or failing, make sure you have enough free storage and a stable connection, restart the device and try again. Do not switch it off in the middle unless it has been stuck for a very long time."),
    ("automatic & update|updates", "Automatic updates install fixes in the background so you do not have to remember. They are recommended for most people, especially for security fixes."),
    ("backup|back & why|important|need|should|protect",
     "A backup protects your files if your device is lost, damaged, stolen or hit by malware, so keep a copy somewhere else."),
    ("backup|back & how|make|create|do|set|often|regular",
     "To back up, copy your important files to an external drive or a cloud service, ideally automatically, and keep more than one copy. Check now and then that you can restore from them."),
    ("backup|back & phone|iphone|android|photo|picture",
     "You can back up a phone using its built in cloud backup in settings or by copying photos and files to a computer. Turn on automatic backup so it stays current."),
    ("cloud & storage|backup|what|is|mean", "Cloud storage keeps your files on internet servers so you can reach them from any device and have a copy if your device fails."),
    ("cloud & safe|secure|private", "Cloud services are generally well protected, but you should still use a strong password and two factor authentication on the account."),
    ("restore & factory|reset|backup|device", "A factory reset erases everything on a device and returns it to its original settings. Back up your files first, since they will be lost."),
    ("321|3-2-1 & backup|rule", "The 3-2-1 backup rule means keep three copies of your data, on two different types of storage, with one copy kept offsite."),
    ("sync|synchronize|syncing", "Syncing keeps the same files or settings up to date across your devices through an account. It is not the same as a backup, since deleting a file may delete it everywhere."),
    # ---- storage, hardware, terms ----
    ("ram|memory & storage|difference|different|vs|versus|disk",
     "RAM is short term memory the computer uses while it is running, while storage keeps your files even when the computer is off."),
    ("ram|memory & what|mean|is|does", "RAM is the short term working memory a computer uses for the programs that are running. More RAM lets it handle more tasks at once."),
    ("storage & full|free|space|out|low|clear|run",
     "To free up storage, delete files and apps you do not use, empty the trash, clear downloads and move photos and videos to the cloud or an external drive."),
    ("ssd|hdd|hard & drive|disk|solid & difference|different|vs|faster",
     "A solid state drive has no moving parts and is usually faster and quieter, while a hard disk drive uses spinning platters and is often cheaper for large storage."),
    ("cpu|processor", "The CPU, or processor, is the part of a computer that carries out instructions and does the main calculating."),
    ("gpu|graphics & card", "A GPU, or graphics processor, handles images, video and games, and is also used for heavy parallel calculations."),
    ("motherboard", "The motherboard is the main circuit board that connects a computer's processor, memory, storage and other parts."),
    ("operating & system|os", "An operating system is the main software that manages a device's hardware and runs your apps, for example on a computer or phone."),
    ("bit|byte|megabyte|gigabyte|terabyte|kilobyte & what|difference|mean|is|bigger",
     "A byte is a small unit of data, and kilobytes, megabytes, gigabytes and terabytes are successively larger amounts of storage."),
    ("gb|gigabyte|terabyte|tb & much|many|enough|need|choose|storage",
     "How much storage you need depends on what you keep. Photos, videos and games take the most space, so check what you use now and leave some room to spare."),
    ("bluetooth", "Bluetooth is a short range wireless technology that connects devices such as headphones, speakers and keyboards to your phone or computer."),
    ("usb & what|is|difference|type|c|port", "USB is a standard connector and protocol for connecting devices and charging them. Different USB cables and ports can support different speeds and power."),
    ("nfc|contactless", "NFC is a short range wireless technology used for tapping to pay or pair devices."),
    ("resolution|pixel|hd|4k & screen|display|monitor|tv|mean|what", "Screen resolution is the number of pixels a display shows. More pixels generally mean a sharper image."),
    ("refresh & rate|hz|screen", "Refresh rate is how many times per second a screen updates the image. A higher rate looks smoother."),
    ("app & what|mean|is|difference|program", "An app is a software program that does a specific job on a phone, tablet or computer."),
    ("browser & what|mean|is", "A web browser is the app you use to open and view websites."),
    ("search & engine|browser & difference", "A browser is the app you use to visit websites, while a search engine is a website that helps you find pages."),
    ("internet|web & difference|different|www", "The internet is the global network of connected computers, while the web is the collection of pages and sites you view on it using a browser."),
    ("ai|artificial & intelligence|chatbot|what|mean|is", "Artificial intelligence is software that can do tasks that usually need human thinking, like understanding language or recognizing images. It can make mistakes, so check important answers."),
    ("algorithm", "An algorithm is a set of step by step instructions a computer follows to solve a problem or make a decision."),
    ("bug & what|software|mean|is", "A software bug is a mistake in a program that makes it behave in an unexpected way."),
    ("file & format|extension|type|pdf|jpg|png|mp3|zip", "A file extension, such as pdf, jpg or mp3, is the ending of a file name that tells you what type of file it is and which app can open it."),
    ("zip|compress|compression & file|folder", "A zip file bundles and compresses files into one smaller file. Open or extract it to use what is inside."),
    ("pdf & what|mean|is", "A PDF is a file format that keeps a document looking the same on any device."),
    ("screenshot|screen & capture|take|shot", "You can take a screenshot with your device's built in shortcut, usually a button combination on a phone or a key combination on a computer. Check your device's help for the exact keys."),
    ("shortcut|keyboard & copy|paste|useful|common|time", "Common keyboard shortcuts are copy, paste and undo, which are usually the control key, or command on a Mac, with C, V and Z."),
    ("copy & paste", "To copy and paste, select the text or file, choose copy, click where you want it and choose paste. Keyboard shortcuts with the control or command key do the same."),
    ("delete & recover|restore|deleted|undo|accident|file|photo",
     "Deleted files often sit in the trash or recycle bin for a while, so check there first and restore them. Otherwise look for a backup or a recently deleted folder in your photo or cloud app."),
    ("recycle|trash & bin", "The trash or recycle bin holds deleted files temporarily so you can restore them. Emptying it removes them for good."),
    ("ebook|e-book|kindle|reader", "An e-reader or e-book app lets you read digital books on a screen, and you can often change the text size and lighting."),
    ("smart & home|speaker|assistant", "Smart home devices connect to the internet so you can control them with an app or voice. Secure them with strong passwords and updates."),
    ("iot|internet & of & things", "The Internet of Things is everyday devices, like thermostats and cameras, that connect to the internet. Keep them updated and change default passwords."),
    ("battery & last|longer|life|save|drain|preserve|improve",
     "To make a battery last longer, lower the screen brightness, close apps you are not using, turn on battery saver and avoid extreme heat."),
    ("battery & charge|charging & bad|overcharge|best|how|habit|health",
     "Modern devices manage charging themselves, so overnight charging is generally fine. Heat is the bigger enemy, so keep devices cool and avoid leaving them in hot places."),
    ("battery & replace|swollen|bulge|dead|old", "If a battery drains very fast, swells or overheats, stop using it and have it checked or replaced by a qualified repair service."),
    ("charger|charging & not|slow|wo|work|fail|phone",
     "If a phone is not charging, check the cable and charger, clean lint from the port gently, try another outlet and restart the phone."),
    ("overheat|hot|heat|warm & phone|laptop|computer|device",
     "If a device overheats, close heavy apps, take it out of direct sun or a case, let it cool, and keep vents clear. Charge it somewhere ventilated."),
    ("fan & loud|noisy|noise|laptop|computer", "A loud fan usually means the computer is working hard or is dusty. Close heavy programs, keep vents clear and clean dust away gently."),
    ("airplane|flight & mode", "Airplane mode turns off wireless connections like cellular, Wi-Fi and Bluetooth, which saves battery and is used on flights."),
    ("dark & mode", "Dark mode shows light text on a dark background, which can be easier on the eyes in low light and may save battery on some screens."),
    ("notification|alert & too|many|stop|turn|manage|annoying|disable|off",
     "You can manage or turn off notifications in your device settings, app by app. Keep only the ones you really need."),
    ("screen & time|limit|kid|child|parental|control",
     "Parental controls and screen time settings let you set limits, filter content and approve apps for children. Talk with kids about online safety too."),
    ("eye|eyes & strain|screen|tired|computer",
     "To reduce eye strain from screens, take regular breaks to look at something far away, adjust brightness and text size, and keep the screen at a comfortable distance."),
    ("posture|ergonomic|desk & computer|laptop|sit", "Sit with your back supported, the screen at about eye level and your wrists relaxed, and take breaks to move around."),
    # ---- troubleshooting ----
    ("computer|pc|laptop|windows|mac & slow|slowly|sluggish|lag|laggy|speed|faster|performance",
     "Restart the computer, close programs you are not using, and check that you have free disk space. Keeping software updated and removing unneeded startup programs also helps."),
    ("phone|iphone|android & slow|slowly|sluggish|lag|laggy|speed|faster|performance",
     "Restart the phone, close unused apps, free up storage and install pending updates. Removing apps you do not use also helps."),
    ("freeze|frozen|hang|hung|unresponsive|stuck|crash & computer|app|phone|program|screen",
     "If something freezes, wait a moment, then close the app. If the device is still stuck, restart it, and check for updates if it keeps happening."),
    ("restart|reboot & why|work|fix|help|does",
     "Restarting clears temporary problems and frees up memory, and gives the system a fresh start, which fixes many glitches."),
    ("not|wo|wont|will|turn|power|boot|start & computer|laptop|phone|device|on",
     "If a device will not turn on, check the power cable and outlet, charge it for a while, hold the power button for several seconds and try a different charger. If it still fails, contact support or a repair service."),
    ("blue & screen|crash|error", "A system crash or error screen usually points to a software or hardware problem. Restart, install updates, remove recently added software or drivers and, if it repeats, contact support."),
    ("black & screen|blank|display", "If the screen is black, check that the device is on and charged, check cables and brightness, then try restarting it."),
    ("app & crash|crashing|close|freeze|won|work|not|keep",
     "If an app keeps crashing, update it, restart your device, clear its cache and, if needed, uninstall and reinstall it."),
    ("uninstall|delete|remove & app|program|software", "To remove an app, find it in your device settings or apps list and choose uninstall, or press and hold the icon on a phone."),
    ("install|download & app|program|software", "To install an app, open your device's official app store, search for it, check the publisher and tap install."),
    ("sound|audio|volume|speaker & no|not|wo|work|fix|mute|hear",
     "If there is no sound, check the volume and mute settings, the selected output device, and cables or Bluetooth connections, then restart the device."),
    ("microphone|mic & no|not|work|wo|fix|hear", "If your microphone is not working, check the app's permission, make sure the right input device is selected, check the mute switch and restart the app."),
    ("camera|webcam & no|not|work|wo|fix|black", "If the camera is not working, check the app has permission, close other apps using it, check any cover or privacy switch and restart the device."),
    ("printer & not|wo|work|print|fix|offline", "If the printer is not printing, check it is on, connected and has paper and ink, clear any queue, restart the printer and computer and check the connection."),
    ("screen & crack|broken|damage|repair", "A cracked screen can get worse and may cut you. Back up your data, use a screen protector or case to prevent it, and visit a reliable repair service."),
    ("water|wet|liquid|spill & phone|laptop|device|keyboard|drop|damage",
     "If a device gets wet, switch it off at once, unplug it, dry the outside and let it dry for a day or more. Do not charge it or use heat, and rice is not a reliable fix."),
    ("keyboard & not|wo|work|type|stuck|key", "If a keyboard is not working, check the connection or batteries, try another USB port or reconnect Bluetooth, and restart the computer."),
    ("mouse|trackpad & not|wo|work|move|cursor", "If the mouse is not working, check its batteries or cable, try another port, reconnect it and restart the computer."),
    ("storage|disk & not|enough|insufficient|error|full", "If you see a storage full message, delete unneeded files and apps, clear caches and move photos or files to the cloud or an external drive."),
    ("safe & mode", "Safe mode starts a computer with only essential software, which helps you find and fix problems caused by apps or drivers."),
    ("driver", "A driver is software that lets your operating system communicate with a hardware device, such as a printer. Keeping drivers updated can fix problems."),
    ("firmware", "Firmware is the low level software built into a device that controls its hardware. Updating it can fix bugs and improve security."),
    ("defrag|defragment", "Defragmenting rearranges data on old spinning hard drives to speed them up. It is not needed on solid state drives."),
    ("pop & ads|adware|unwanted|browser|redirect", "Unwanted pop ups or redirects can be a sign of adware. Remove unknown extensions, update your browser and run a security scan."),
    ("extension|add-on|addon|plugin & browser|chrome|firefox|safari", "Browser extensions add features, but they can read your browsing. Install only the ones you need from official sources and remove those you do not use."),
    ("tab & many|browser|slow|memory", "Having many tabs open uses memory and can slow your computer, so close the ones you do not need."),
    ("bookmark", "A bookmark saves a web page address in your browser so you can easily return to it later."),
    ("default & browser|search", "You can change your default browser or search engine in your device or browser settings."),
    ("download & slow|fail|stuck|file|browser", "If a download is slow or failing, check your connection, pause other downloads, try again later or use a different network."),
    # ---- networks and wifi ----
    ("wifi|wi-fi|wireless|internet|connection & slow|speed|faster|improve|boost|weak|signal|lag",
     "To improve slow Wi-Fi, restart your router, move closer or place it in a central open spot, reduce the number of connected devices and check for interference. If it stays slow, contact your internet provider."),
    ("wifi|wi-fi|internet & not|wo|work|connect|down|drop|fix|disconnect|keep",
     "If your internet is not working, restart your router and device, check that other devices are connected, check cables and contact your provider if it is down."),
    ("router & restart|reset|reboot|why|how", "Restarting the router clears temporary problems. Unplug it, wait about thirty seconds, plug it back in and wait for it to reconnect."),
    ("router|modem & difference|different|what|is|mean", "A modem connects your home to your internet provider, while a router shares that connection with your devices, often over Wi-Fi."),
    ("wifi|wi-fi & what|mean|is|stand", "Wi-Fi is a wireless technology that connects your devices to a network and the internet through a router."),
    ("wifi|wi-fi|router & password|secure|safe|protect|wpa|encryption",
     "Secure your Wi-Fi with a strong, unique network password, modern WPA encryption and a changed router admin password, and keep the router firmware updated."),
    ("ip & address", "An IP address is a number that identifies a device on a network, like an address for sending data to the right place."),
    ("dns", "DNS is the system that turns website names into the numeric addresses computers use, like a phone book for the internet."),
    ("bandwidth|speed|mbps & what|mean|is|internet|test", "Bandwidth is how much data a connection can carry at once, and it is usually measured in megabits per second. Higher is faster for downloads and streaming."),
    ("ping|latency", "Latency, or ping, is the delay for data to travel to a server and back. Lower is better, especially for gaming and video calls."),
    ("ethernet|cable|wired & wifi|better|faster|vs|difference", "A wired Ethernet connection is usually faster and more stable than Wi-Fi, while Wi-Fi is more convenient."),
    ("24|5 & ghz|band|wifi|wi-fi", "The 2.4 GHz Wi-Fi band reaches further but is usually slower, while 5 GHz is usually faster over shorter distances."),
    ("mobile|cellular|data & use|save|reduce|less|too|much|usage|limit",
     "To use less mobile data, connect to Wi-Fi when you can, turn on data saver, limit background app refresh and download videos and music on Wi-Fi."),
    ("hotspot|tether|tethering", "A mobile hotspot shares your phone's internet connection with other devices. It uses your mobile data and battery."),
    ("5g|4g|lte|3g & what|mean|is|difference", "5G, 4G and LTE are generations of mobile network technology, and newer generations generally offer faster speeds and quicker response."),
    ("extender|mesh|booster|repeater|dead & zone|wifi|range", "A Wi-Fi extender or mesh system can improve coverage in areas your router does not reach well."),
    ("guest & network|wifi", "A guest Wi-Fi network lets visitors get online without access to your main devices and files."),
    ("stream|streaming|buffer|buffering & video|movie|slow|stop|keep|lag",
     "If video keeps buffering, check your connection speed, pause other downloads, restart your router, lower the video quality or move closer to the router."),
    ("video & call|meeting|zoom|conference & quality|bad|better|lag|freeze|improve",
     "For better video calls, use a stable connection, ideally wired or close to the router, close other apps, use a headset and make sure you have good lighting."),
    # ---- email, messaging, social ----
    ("email & full|inbox|clean|organize|manage|too|many|overload",
     "To manage a crowded inbox, unsubscribe from newsletters you do not read, use folders, labels and filters, delete or archive old messages and set times to check email."),
    ("email & address|create|make|setup|set|new|account|sign", "To create an email account, pick a provider, choose a unique address and a strong password, and add recovery details."),
    ("cc|bcc & email|mean|what|difference", "Cc sends a copy of an email to others, visible to everyone, while Bcc sends a copy without showing those recipients to the other people."),
    ("email & recall|undo|unsend|wrong|mistake", "Many email apps offer a short undo send window in settings, but once a message is delivered you generally cannot take it back."),
    ("unsubscribe", "To stop unwanted newsletters, use the unsubscribe link from a sender you trust. For suspicious spam, do not click anything and just mark it as spam."),
    ("email & not|wo|receive|get|arriving|missing|send|sending", "If email is not arriving or sending, check your connection, spam and storage, confirm the address is right, and check your account settings or server status."),
    ("attachment & too|big|large|size|limit|send|share", "If an attachment is too large, compress it into a zip, or upload it to a cloud service and share a link instead."),
    ("message|text|chat & encrypted|end|private|secure|safe", "End to end encryption means only you and the person you message can read it. Check your messaging app's settings for it."),
    ("emoji", "An emoji is a small digital picture used in messages to show an idea or feeling."),
    ("social & media & what|is|mean", "Social media is online platforms where people share posts, photos and messages and connect with others."),
    ("fake & news|information|misinformation|check|verify|spot|identify|false",
     "To check if online information is true, look at the source, see whether trusted outlets report the same thing, check the date and be cautious of shocking claims."),
    ("review|rating & fake|trust|reliable|online|product", "To judge online reviews, read a range of them, look for specific details, be cautious of ones that are all very similar or extreme, and check more than one source."),
    ("shopping|buy|purchase|pay & online|safe|secure|safely", "For safe online shopping, use well known sites with HTTPS, a secure payment method, strong passwords and be wary of deals that seem too good to be true."),
    ("scam|fake & website|shop|store|online|check|legit|legitimate", "To check a site is legitimate, look for the correct web address, contact details, reviews from independent sources and secure payment, and be wary of unrealistic prices."),
    ("share|post|tell & password|pin|code|bank", "Never share your passwords, PINs or one time codes with anyone, including people claiming to be from a company or support team."),
    ("cyberbullying|bullying|harass|online", "If you face online bullying or harassment, do not engage, keep screenshots, block and report the person to the platform, and tell someone you trust."),
    ("children|kid|child & online|safe|internet|protect|device", "Keep children safe online with parental controls, open conversations about what they see, privacy settings and age appropriate apps."),
    # ---- software and everyday how-to ----
    ("free & software|app|program|trial|safe", "Free apps are often funded by ads or data collection, so read the permissions and privacy policy and install from official stores."),
    ("subscription|cancel & app|service|trial", "To cancel a subscription, go to the account or subscriptions section of the app store or service and turn off renewal before the billing date."),
    ("open & source", "Open source software is software whose code is public so anyone can inspect, use and often modify it."),
    ("beta & software|app|what|mean", "A beta is an early version of software released for testing, so it may contain bugs."),
    ("license|licence & software|key", "A software license sets the terms for how you may use a program. Use legitimate copies, since pirated software can carry malware."),
    ("document|word|spreadsheet|excel|slide|office & free|alternative|open", "Many free office apps can create and edit documents, spreadsheets and presentations, and most can save in common file formats."),
    ("compatible|compatibility & app|software|device|file", "Check an app's requirements to confirm it supports your device and operating system version before installing."),
    ("language & change|keyboard|device|phone|computer", "You can change the language and keyboard in your device's settings under language or region."),
    ("font|text & size|bigger|larger|readable|small", "You can make text bigger in your device's accessibility or display settings."),
    ("accessibility|disabled|visual|hearing & feature|device|setting|option", "Devices include accessibility settings like screen readers, larger text, captions and voice control. Look in settings under accessibility."),
    ("voice & assistant|control|command", "A voice assistant listens for a wake word and carries out spoken requests. You can review its privacy and listening settings in the app."),
    ("smartwatch|wearable|fitness & tracker|watch", "A smartwatch or fitness tracker records things like steps and heart rate and shows notifications. Check its privacy settings for what it shares."),
    ("drone", "A drone is a flying device controlled remotely. Check local rules before flying it, since many places restrict where you can use one."),
    ("3d & print|printer|printing", "3D printing builds a physical object layer by layer from a digital design."),
    ("blockchain", "A blockchain is a shared digital record kept across many computers in a way that makes past entries hard to change."),
    ("crypto|cryptocurrency|bitcoin & what|mean|is", "Cryptocurrency is digital money secured by cryptography. Its value can change quickly, so be cautious and wary of scams promising easy returns."),
    ("cloud & computing|what|mean", "Cloud computing means using servers on the internet to store data or run software, rather than on your own device."),
    ("website|domain|web & address|url|what|mean", "A URL is a web address that tells your browser where to find a page, and the domain is the main name part of it."),
    ("wallpaper|home & screen|customize|personalize", "You can personalize your device in settings, where you can change the wallpaper, theme and layout."),
    ("recycle|dispose|old|throw & phone|laptop|electronics|device|e-waste|battery",
     "Do not throw old electronics in the regular trash. Wipe your data, then take them to a recycling or trade in program or an electronics collection point."),
    ("sell|give|trade|donate|wipe|erase & old|phone|laptop|device|computer|data",
     "Before selling or giving away a device, back up your data, sign out of your accounts and do a factory reset to erase it."),
    ("new|buy|choose|pick & phone|laptop|computer|device|tablet",
     "When choosing a device, decide what you will use it for, then compare storage, battery life, screen, update support and your budget, and read independent reviews."),
    ("warranty|repair|fix & device|phone|laptop|broken", "Check your warranty or protection plan first, then use an authorized or well reviewed repair service, and back up your data beforehand."),
]

_COMPILED = []
for _spec, _answer in RULES:
    _groups = []
    for _g in _spec.split("&"):
        _alts = {_stem(a.strip().lower()) for a in _g.split("|") if a.strip()}
        if _alts:
            _groups.append(_alts)
    _COMPILED.append((_groups, _answer))

_WORD = re.compile(r"[a-z0-9-]+")


def propose(ctx: "Context") -> Optional[Proposal]:
    toks = set()
    for t in ctx.tokens:
        toks.add(_stem(t))
    for t in _WORD.findall(ctx.text):
        toks.add(_stem(t))
    best = None
    best_key = None
    for idx, (groups, answer) in enumerate(_COMPILED):
        # first group is the topic and must match; later groups are optional boosters
        if not (groups[0] & toks):
            continue
        hits = [bool(g & toks) for g in groups[1:]]
        if len(groups) > 1 and not any(hits):
            # a topic word alone is not enough for rules that require context
            continue
        key = (sum(hits), -idx)
        if best_key is None or key > best_key:
            best_key, best = key, answer
    if best is None:
        return None
    return Proposal(best, min(0.7 + 0.04 * best_key[0], 0.85))
