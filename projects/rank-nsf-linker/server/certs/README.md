# Certs

## 1. Generate Server Certs

```sh
# Private key
openssl genrsa -out server.key 4096

# CSR with SAN from openssl-san.cnf
openssl req -new -key server.key -out server.csr \
  -config openssl-san.cnf

# Secure permissions
chmod 600 server.key
chmod 644 server.csr
```

## 2. Generate Self-Signed CA

```sh
openssl genrsa -out ca.key 4096

openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 -out ca.crt \
  -subj "/C=US/ST=State/L=City/O=MyOrg/CN=MyRootCA"
```

## 3. Sign Server with Self-Signed CA

```sh
openssl x509 -req -in server.csr \
  -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out server.crt -days 365 -sha256 \
  -extfile openssl-san.cnf -extensions req_ext
```

## 4. Generate Client Certificate (signed by same CA)

```sh
# Client key
openssl genrsa -out client.key 4096

# Client CSR
openssl req -new -key client.key -out client.csr \
  -subj "/C=US/ST=State/L=City/O=MyOrg/CN=go-server"

# Sign client cert with CA
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out client.crt -days 365 -sha256
```
