---
layout: default
title: Fixing SSL Verification Error for Ruby on Windows (Zscaler Root CA Issue)
comments: true
date: 2024-12-24
categories:
---

## Fixing SSL Verification Error for Ruby on Windows (Zscaler Root CA Issue)

When using Ruby on Windows, you may encounter the following SSL error when trying to install gems or access HTTPS sites:

```
ERROR: SSL verification error at depth 2: unable to get local issuer certificate (20)
You must add /C=US/ST=California/L=San Jose/O=Zscaler Inc./OU=Zscaler Inc./CN=Zscaler Root CA/emailAddress=support@zscaler.com to your local trusted store
```

### **Cause:**
This error occurs because Zscaler intercepts SSL traffic and re-signs certificates with its own root CA, which Ruby and OpenSSL do not automatically trust. To resolve this, you need to import the Zscaler Root CA into Ruby's trusted certificate store.

---

### **Fixing the Error:**

### **Step 1: Export the Zscaler Root Certificate**
1. Open **Chrome** or **Edge** and visit any HTTPS site (e.g., `https://rubygems.org`).
2. Click on the **padlock icon** in the address bar.
3. Select **Connection is secure** > **Certificate (Valid)**.
4. In the **Certification Path** tab, select the **Zscaler Root CA** (top-level certificate).
5. Click **View Certificate** > **Details** > **Copy to File...**.
6. Choose **Base-64 encoded X.509 (.CER)** format.
7. Save the file as `Zscaler_Root_CA.crt`.

---

### **Step 2: Convert to PEM Format (if necessary)**
1. Open Command Prompt as Administrator.
2. Run the following command to convert the `.crt` to `.pem`:
   ```bash
   openssl x509 -inform DER -outform PEM -in "C:\Users\<username>\Downloads\Zscaler_Root_CA.crt" -out "C:\Users\<username>\Downloads\Zscaler_Root_CA.pem"
   ```
3. If the file already has the following format, no conversion is necessary:
   ```
   -----BEGIN CERTIFICATE-----
   (base64 encoded content)
   -----END CERTIFICATE-----
   ```

---

### **Step 3: Add Certificate to Ruby's Trusted Store**
1. Copy the certificate to Ruby's SSL directory:
   ```bash
   copy C:\Users\<username>\Downloads\Zscaler_Root_CA.pem C:\Ruby33-x64\bin\etc\ssl\certs\
   ```
2. Run the following command to create symbolic links for the certificate:
   ```bash
   cd C:\Ruby33-x64\bin\etc\ssl\certs
   ruby c_rehash.rb
   ```

---

### **Step 4: Verify Certificate Installation**
1. Run the following command to verify the certificate:
   ```bash
   openssl verify -CAfile C:\Ruby33-x64\bin\etc\ssl\cert.pem Zscaler_Root_CA.pem
   ```
2. If the result shows:
   ```
   Zscaler_Root_CA.pem: OK
   ```
   The certificate is correctly trusted.

---

### **Step 5: Test Gem Installation**
Now test if the SSL issue is resolved:
```bash
gem install bundler
```

---

### **Alternative Method: Append to cert.pem**
If the error persists, manually append the certificate to Ruby's CA bundle:
```bash
type Zscaler_Root_CA.pem >> C:\Ruby33-x64\bin\etc\ssl\cert.pem
```

---

### **Set SSL_CERT_FILE Permanently**
To ensure Ruby always uses the correct certificate:
1. Open **Control Panel** > **System** > **Advanced System Settings** > **Environment Variables**.
2. Add a new system variable:
   ```
   Variable: SSL_CERT_FILE
   Value: C:\Ruby33-x64\bin\etc\ssl\cert.pem
   ```

---

### **If the Issue Persists:**
- Ensure the correct **Root CA** is exported (not the intermediate or leaf certificate).
- Restart Command Prompt and retry.
- Contact your IT team to obtain the latest Zscaler Root CA.

By following these steps, Ruby should now trust Zscaler certificates, allowing smooth installation of gems and other secure operations.
