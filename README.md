# Universal SMS Connector for Odoo 18

![Odoo 18](https://img.shields.io/badge/Odoo-18.0-purple.svg) ![License](https://img.shields.io/badge/License-LGPL--3-blue.svg)

**Bypass Odoo IAP and use your own local SMS gateways directly.**

This module integrates external SMS providers (Boomcast, MiMSMS, AWS SNS) into Odoo's native ecosystem. It allows you to send SMS messages directly from the Contacts, CRM, and Marketing apps using your own API credentials, bypassing the expensive Odoo IAP credits.

## 🚀 Key Features

* **Native Integration:** Overrides Odoo's core SMS sending. Clicking the "SMS" icon on a contact works instantly.
* **Multi-Provider Support:** Switch between providers easily.
* **Smart Number Formatting:**
    * *Boomcast:* Automatically converts `+88017...` to `017...`
    * *MiMSMS:* Automatically converts `017...` to `88017...`
* **Load Balancing:** Set priorities to define which gateway handles traffic.
* **Queue System:** Asynchronous sending via Cron jobs to handle bulk SMS without freezing the server.
* **Delivery Logs:** Full history of API requests, responses, and transaction IDs.
* **Cost Saving:** Use local Bangladeshi gateways for a fraction of the cost of international credits.

## 🔌 Supported Providers

| Provider | Country | Type | Features |
| :--- | :--- | :--- | :--- |
| **Boomcast** | Bangladesh 🇧🇩 | HTTP/GET | Auto-masking 'NOMASK', Number Cleaner |
| **MiMSMS** | Bangladesh 🇧🇩 | JSON/POST | Unicode Support, Auto-prefix '88' |
| **AWS SNS** | Global 🌏 | AWS SDK | High reliability, Worldwide coverage |
| **Generic** | Any | HTTP | Basic implementation for other gateways |

## 🛠️ Installation

1.  **Clone the repository** into your Odoo addons path:
    ```bash
    cd /path/to/your/custom/addons
    git clone [https://github.com/TorabRamin/universal_sms_connector.git](https://github.com/TorabRamin/universal_sms_connector.git)
    ```

2.  **Install Dependencies** (Required for AWS SNS):
    ```bash
    pip3 install boto3
    ```

3.  **Restart Odoo:**
    ```bash
    sudo service odoo restart
    ```

4.  **Activate:**
    * Go to **Apps**.
    * Click **Update Apps List**.
    * Search for **Universal SMS Connector**.
    * Click **Activate**.

## ⚙️ Configuration

1.  Navigate to **SMS Gateway > Providers**.
2.  Click **New**.
3.  **Select Provider Type:** (e.g., *Boomcast (BD)*).
4.  **Enter Credentials:**
    * *Base URL:* Provided by your gateway.
    * *Username / Password / API Key.*
5.  **Set State:** Enable the provider.
6.  **Priority:** Set to `1` for your primary gateway.

### Example: Boomcast Setup
* **URL:** `http://api.boom-cast.com/.../externalApiSendTextMessage.php`
* **Username:** `01xxxxxxxxx`
* **Masking:** `NOMASK` (or your Brand Name)

## 📱 How to Use

### Method 1: The Native Way (Recommended)
You don't need to change your workflow.
1.  Go to **Contacts** or **CRM**.
2.  Click the standard **SMS Icon** 💬 next to a phone number.
3.  Type your message and hit **Send**.
4.  The module intercepts the message, routes it through your local gateway, and logs the success in the chatter.

### Method 2: Bulk / Manual Wizard
1.  Go to **SMS Gateway > Send SMS**.
2.  Select Recipients.
3.  Type your message (Character counter included).
4.  Click **Send Now**.

## 📊 Logging & Troubleshooting
Every single SMS attempt is recorded.
* Go to **SMS Gateway > Logs**.
* View the **Technical Data** tab to see the raw response from the API (Success, Invalid Number, Balance Error, etc.).

## ⚠️ Compatibility
* **Odoo Version:** 18.0 (Strict)
* **Python:** 3.10+

## 👨‍💻 Author & Connect

**Developed by Torab Ramin**

* **GitHub:** [TorabRamin](http://github.com/TorabRamin/)
* **Facebook:** [TorabRamin](https://www.facebook.com/TorabRamin/)
* **Website:** [torab.me](https://torab.me)