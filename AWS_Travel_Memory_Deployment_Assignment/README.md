# Travel Memory Deployment Assignment

This project is created for deploying the Travel Memory application from the GitHub repository:

https://github.com/UnpredictablePrashant/TravelMemory

## Project Purpose

The goal of this assignment is to deploy the Travel Memory application on AWS using EC2 instances, configure the backend environment, and prepare the application for access through the internet.

This deployment involves running the project on EC2 instances, configuring Nginx as a reverse proxy, and following a three-tier architecture approach.

## Three-Tier Architecture Overview

A three-tier architecture separates the application into three layers:

- Presentation tier: the frontend interface that users interact with
- Application tier: the backend logic that processes requests and business rules
- Data tier: the database layer that stores and retrieves application data

This design improves scalability, maintainability, and easier troubleshooting compared to placing everything on a single server.

### Real-World Example

A simple real-world analogy is an online restaurant system:

- Frontend / Presentation tier: the customer-facing website or app
- Backend / Application tier: the kitchen and order management system
- Database / Data tier: the inventory and order records storage

In the same way, the Travel Memory application uses separate layers for user interaction, application logic, and data storage.

## Deployment Approach

The deployment will follow a layered AWS architecture to make the application available through a custom domain and backend API:

1. Users access the frontend through Cloudflare DNS using the custom domain travelmemory.travelmemory.adityabhagvathdevops.site.
2. The frontend is hosted on EC2 instances behind an Application Load Balancer (ALB) named aditya-mern-frontend.
3. The frontend instances run the React application behind Nginx on port 80 and are configured to connect to the backend domain.
4. The backend is exposed through a second domain such as back.travelmemory.adityabhagvathdevops.site and is served by a separate backend ALB.
5. Backend EC2 instances run the Node.js application on port 3000 and use Nginx as a reverse proxy on port 80.
6. The backend connects to MongoDB Atlas, where the travelmemory cluster is used as the cloud database and access is restricted to whitelisted IPs.

This approach provides a scalable and production-style layout for the Travel Memory application.

## Instance Reference Table

| Server | Instance Name | Public IP | Private IP | AZ |
|--------|---------------|-----------|------------|----|
| Backend Primary | aditya_mern_backend | 52.201.49.154 | 172.31.31.237 | us-east-1c |
| Backend Replica | aditya_mern_backend2 | 3.83.24.50 | 172.31.81.10 | us-east-1b |
| Frontend Primary | aditya_mern_frontend | 3.82.52.108 | 172.31.21.58 | us-east-1c |
| Frontend Replica | aditya_mern_frontend2 | 32.198.93.215 | 172.31.91.217 | us-east-1b |

## VPC Configuration (AWS Console)

Create the VPC and networking components from the AWS Console before launching the EC2 instances.

### 1. Create the VPC

- Go to AWS Console → VPC.
- Click Create VPC.
- Choose VPC only.
- Enter a name such as `travel-memory-vpc`.
- Set the CIDR block to `10.0.0.0/16`.
- Create the VPC.

### 2. Create Public and Private Subnets

Create four subnets in two Availability Zones:

- Public subnet 1: `10.0.1.0/24` in `us-east-1c`
- Public subnet 2: `10.0.2.0/24` in `us-east-1b`
- Private subnet 1: `10.0.3.0/24` in `us-east-1c`
- Private subnet 2: `10.0.4.0/24` in `us-east-1b`

These subnets will support the frontend and backend tier placement.

### 3. Create an Internet Gateway

- Go to Internet Gateways.
- Create an Internet Gateway.
- Attach it to the VPC.

### 4. Create Route Tables

- Create one public route table and associate it with the public subnets.
- Add a route `0.0.0.0/0` pointing to the Internet Gateway.
- Create one private route table and associate it with the private subnets.

### 5. Create Security Groups

Create security groups for the application tiers:

- Frontend security group:
  - Allow SSH (22)
  - Allow HTTP (80)
  - Allow HTTPS (443)
- Backend security group:
  - Allow SSH (22)
  - Allow HTTP (80)
  - Allow HTTPS (443)
  - Allow port `3000` for the Node.js backend

### 6. Optional NAT Gateway

If private subnets need outbound internet access, create a NAT Gateway in a public subnet and update the private route table.

### 7. Verify the VPC Setup

Confirm the following before launching instances:

- VPC is created successfully
- Public and private subnets exist
- Internet Gateway is attached
- Route tables are configured correctly
- Security groups allow the required ports

## Task 1 — Backend EC2 Setup

### 1.1 Launch the Backend EC2 Instance

Think of this as renting a server in the cloud, similar to renting a kitchen where your application will run and respond to requests.

Go to AWS Console → EC2 → Launch Instance.

| Setting | Value |
|---------|-------|
| Instance Name | aditya_mern_backend |
| AMI | Ubuntu Server 22.04 LTS (64-bit x86) |
| Instance Type | t2.micro (Free Tier eligible) |
| Key Pair | aditya-RSA-key-AWS (create a new one if needed) |
| Network | Created VPC `vpc-04971687160e2c7fe` |
| Auto-assign Public IP | Enable |
| Security Group | Select an existing backend security group that allows SSH, HTTP, HTTPS, and port `3000` |

Launch the instance and note the public IP address after it is running.

### 1.2 Configure User Data for Backend Setup

In the Advanced → User Data section, paste the following script. This script runs automatically when the server starts, similar to a checklist the new kitchen follows on its first day.

```bash
#!/bin/bash
sudo apt-get update
sudo curl -s https://deb.nodesource.com/setup_18.x | sudo bash
sudo apt install -y nodejs
sudo apt update
cd /home/ubuntu/
sudo git clone https://github.com/UnpredictablePrashant/TravelMemory
```

What this does:

- `apt-get update` refreshes the list of available packages.
- `nodesource setup` adds the Node.js 18 package source.
- `apt install nodejs` installs Node.js, which runs the backend application.
- `git clone` downloads the TravelMemory application code from GitHub.

### 1.3 Create the MongoDB Atlas Cluster

Follow these steps to create the database cluster and obtain the connection string for the backend:

1. Go to MongoDB Atlas: https://account.mongodb.com/account/login
2. Sign in or create a new account.
3. Create a new project (if needed) and name it `travelmemory`.
4. Click "Build a Database" and choose the free tier cluster option.
5. Select the cloud provider and region, then create the cluster.
6. Wait for the cluster to finish provisioning.
7. In the "Network Access" section, add a new IP access entry with:
   - IP Address: `0.0.0.0`
   - Comment: `Allow all traffic`
8. In the "Database Access" section, create a database user with a username and password.
9. In the "Connect" section, choose "Connect your application" and copy the connection string.
10. Use the cluster name `travelmemory`, which will generate a connection string in the following format:

```text
mongodb+srv://<username>:<password>@travelmemory.ax43th5.mongodb.net/travelmemory
```

For this assignment, the generated MongoDB URI is:

```env
MONGO_URI='mongodb+srv://adityabhagvath1994_db_user:kuRDJK2NqaodRa7Y@travelmemory.ax43th5.mongodb.net/travelmemory'
```

### 1.4 Configure the Backend Environment

SSH into the backend instance and set up the environment file:

```bash
ssh -i aditya-RSA-key-AWS.pem ubuntu@10.0.1.50
cd /home/ubuntu/TravelMemory/backend
ls
```

Expected output:

```bash
conn.js controllers index.js models package-lock.json package.json routes
```

Create the environment file:

```bash
nano .env
```

Add these values to the `.env` file:

```env
MONGO_URI='mongodb+srv://adityabhagvath1994_db_user:kuRDJK2NqaodRa7Y@travelmemory.ax43th5.mongodb.net/travelmemory'
PORT=3000
```

If you get permission issues while editing the file, use:

```bash
sudo nano .env
```

### 1.5 Install Dependencies and Start the Backend

Install the Node.js dependencies and start the backend server:

```bash
cd /home/ubuntu/TravelMemory/backend
sudo npm install
sudo node index.js
```

These commands install the required packages for the backend and launch the Node.js application.

Expected terminal output:

```text
Node.js v18.17.1
Server started at http://localhost:3000
```

Verify in browser:

Open http://10.0.1.50:3000. You will see "Cannot GET /" — this is correct. It means the server is running but there is no route at `/`. The API routes (for example, `/trip` or `/hello`) will respond properly.

### 1.6 Whitelist Backend IP in MongoDB Atlas

Analogy: MongoDB Atlas is a locked pantry. By default, nobody can access it from the outside. You need to add your backend server's IP to the "allowed list" — like giving the kitchen a key to the pantry.

1. Login to cloud.mongodb.com
2. Go to your `travelmemory` cluster → Network Access
3. Click Add IP Address
4. Enter `52.201.49.154` (your backend EC2 public IP)
5. Click Confirm

Important: Do this for BOTH backend instances when you scale later (`52.201.49.154` and `107.22.40.5`). Without this step, the backend cannot connect to the database.

After whitelisting the IPs, test the connection again by running:

```bash
sudo node index.js
```

If the connection is successful, the server should start normally and the backend should be able to reach MongoDB Atlas. If you still see connection errors, check the MongoDB username, password, network access rules, and whether the correct IP was added.

## Task 2 — Configure Nginx on the Backend

### 2.1 Install Nginx as Reverse Proxy on Backend

Analogy: Right now, your kitchen serves food through window `3000`. But customers expect to come to the main entrance (`80`). Nginx is a receptionist who stands at the front door (`80`) and quietly redirects all orders to window `3000`.

Install Nginx:

```bash
sudo apt install nginx -y
```

Verify Nginx is running:

```bash
sudo systemctl status nginx
```

You should see `Active: active (running)` in the output.

Verify in browser:

Open http://52.201.49.154/. You should see the "Welcome to Nginx!" default page.

### 2.2 Configure Nginx as a Reverse Proxy

Now configure Nginx as a reverse proxy:

```bash
sudo unlink /etc/nginx/sites-enabled/default
cd /etc/nginx/sites-available/
sudo nano custom_server.conf
```

Paste the following configuration:

```nginx
server {
    listen 80;
    location / {
        proxy_pass http://localhost:3000;
    }
}
```

What this means: Nginx will forward all requests received on port `80` to the Node.js application running on port `3000`.

Enable the new configuration:

```bash
sudo ln -s /etc/nginx/sites-available/custom_server.conf /etc/nginx/sites-enabled/custom_server.conf
```

Test the configuration for syntax errors:

```bash
sudo service nginx configtest
sudo nginx -t
```

Expected output:

```text
[ OK ]
```

Restart Nginx to apply the changes:

```bash
sudo service nginx restart
```

Verify the reverse proxy:

Open http://52.201.49.154/ in your browser. You should now see "Cannot GET /" — that means the Node.js backend is responding through Nginx on port `80`.


Please Note: Please make sure that node is running parallely on another terminal with the command

```bash
cd TravelMemory/backend/
sudo node index.js
```

## Task 3 — Frontend EC2 Setup

### 3.1 Launch the Backend EC2 Instance

Now think of this as we're setting up the dining hall — what the customer actually sees and interacts with.

Go to AWS Console → EC2 → Launch Instance.

| Setting | Value |
|---------|-------|
| Instance Name | aditya_mern_frontend |
| AMI | Ubuntu Server 22.04 LTS (64-bit x86) |
| Instance Type | t2.micro (Free Tier eligible) |
| Key Pair | aditya-RSA-key-AWS (create a new one if needed) |
| Network | Created VPC `vpc-04971687160e2c7fe` |
| Auto-assign Public IP | Enable |
| Security Group | Select a frontend security group that allows SSH, HTTP, HTTPS, and ports `3000-3001` |

Launch the instance and note the public IP address after it is running.

### 3.2 Configure Frontend to Point to Backend and Install Dependencies and Run Frontend

SSH into the frontend instance and set up the environment file:

```bash
ssh -i aditya-RSA-key-AWS.pem ubuntu@10.0.1.50
cd /home/ubuntu/TravelMemory/frontend
ls
```

Expected output:

```bash
README.md  package-lock.json  package.json  public  src
```

Test the application with the default configurations to check if it is working:

```bash
sudo npm install
# Start the React development server
sudo npm start
```

If the development server starts without any issues, then end the task and edit the src/url.js file: 

```bash
sudo nano src/url.js
```
Update the value as below:

export const baseUrl = "http://52.201.49.154/" 

Verify if the URL has been updated:

```bash
cat src/url.js
```

Install the Dependencies and Run the React development server, post changing of the URL in the src/url.js:

```bash
cd /home/ubuntu/TravelMemory/frontend
sudo npm install
sudo npm start
```

If in case the port shows up as occupied and needs to be killed, then follow the below steps:

```bash
# This will show the port number, replace the PORT_NUMBER with the value and the output of this is the Process ID
sudo ss -lptn 'sport = :PORT_NUMBER'
# With the value received, replace the PID (Process ID) and that will free up the port
sudo kill -9 PID
```

### 3.3 Setting Up Ngnix Reverse Proxy on Frontend

Here, we need to repeat the same steps as done on the backend. Nginx will forward port `80` → port `3000` (where React runs).

```bash
sudo apt install nginx -y
sudo unlink /etc/nginx/sites-enabled/default 
cd /etc/nginx/sites-available/ 
sudo nano custom_server.conf
```

Paste the following configuration:

```nginx
server { 
    listen 80; 
    location / { 
        proxy_pass http://localhost:3000; 
    } 
}  
```
What this means: Nginx will forward all requests received on port `80` to the Node.js application running on port `3000`.

Enable the new configuration:

```bash
sudo ln -s /etc/nginx/sites-available/custom_server.conf /etc/nginx/sites-enabled/custom_server.conf
```

Test the configuration for syntax errors:

```bash
sudo service nginx configtest
sudo nginx -t
```

Expected output:

```text
[ OK ]
```

Restart Nginx to apply the changes:

```bash
sudo service nginx restart
```
Verify the reverse proxy:

Open http://100.58.248.158/ in your browser. You should now see the Travel Memory application running at port `80`.

## Task 4 — Scaling the Application (Adding Replicas)

To handle bulk orders, just one kitchen won't be able to handle everything. To handle a huge load of orders, we need more than one kitchen to work with. And the below steps is extremely useful.

### 4.1 Create AMI (Machine Image Snapshot)

We are creating an image of both backend and frontend in this step so that we can avoid any delays in creating another kitchen to cover more ground area:

For the Backend:
1. In EC2 Console, select instance aditya_mern_backend
2. Click Actions → Image and templates → Create Image
3. Set Image name: aditya_mern_backend
4. Click Create Image

For the Frontend:
1. Select instance aditya_mern_frontend
2. Click Actions → Image and templates → Create Image
3. Set Image name: aditya_mern_frontend
4. Click Create Image

Check EC2 → AMIs — you'll see both images listed:
● aditya_mern_backend — ami-0d685c8e859062119
● aditya_mern_frontend — ami-01922fa221514ffed

### 4.2 Launching Replica Instances from AMIs

For Backend Replica (aditya_mern_backend2):
1. Go to EC2 → AMIs → My AMIs
2. Select aditya_mern_backend
3. Click Launch instance from AMI
4. Name: aditya_mern_backend2
5. Instance type: t2.micro, Key pair: aditya-RSA-key-AWS
6. Launch in us-east-1b (different AZ for high availability)

Result: Public IP 3.83.24.50, Private IP 172.31.81.10

For Frontend Replica (aditya_mern_frontend2):
1. Select aditya_mern_frontend from My AMIs
2. Launch with name aditya_mern_frontend2
3. Place in us-east-1b

Result: Public IP 32.198.93.215, Private IP 172.31.91.217

Verify replicas work:
- SSH into aditya_mern_backend2 — you will find the same configuration, the same repository, and the setup already applied.
- SSH into aditya_mern_frontend2 — you will find the same frontend setup already configured.

Remember: Add 3.83.24.50 (backend2's IP) to the MongoDB Atlas IP whitelist as well!

## Task 5 — Configure Load Balancer and Target Groups

A load balancer distributes incoming traffic across multiple servers so the application stays available and scalable.

### 5.1 Create Target Groups

A target group is a collection of servers that the load balancer can forward traffic to. We will create one target group for the frontend servers and one for the backend servers.

#### Frontend Target Group

Go to EC2 → Target groups → Create target group.

| Setting | Value |
|---------|-------|
| Target type | Instances |
| Target group name | aditya-mern-frontend |
| Protocol | HTTP |
| Port | 80 |
| VPC | vpc-0929f4d11be0cef3a |
| Protocol version | HTTP1 |

Click Next and then Register targets:
- Select aditya_mern_frontend (us-east-1c)
- Select aditya_mern_frontend2 (us-east-1b)
- Click Include as pending below
- Click Create target group

#### Backend Target Group

Repeat the same process for the backend target group.

| Setting | Value |
|---------|-------|
| Target group name | aditya-mern-backend |
| Protocol | HTTP |
| Port | 80 |
| VPC | vpc-0929f4d11be0cef3a |
| Protocol version | HTTP1 |

Register targets:
- aditya_mern_backend (us-east-1c)
- aditya_mern_backend2 (us-east-1b)

### 5.2 Create Application Load Balancers (ALB)

A load balancer acts as the traffic manager that distributes incoming requests to the healthy targets in the target groups.

#### Frontend Load Balancer

Go to EC2 → Load Balancers → Create Load Balancer → Application Load Balancer.

| Setting | Value |
|---------|-------|
| Name | aditya-mern-frontend |
| Scheme | Internet-facing |
| IP address type | IPv4 |
| VPC | vpc-0929f4d11be0cef3a |
| Availability Zones | us-east-1a, us-east-1b, us-east-1c |
| Security groups | default |

Listeners and routing:
- Listener 1: Protocol HTTP, Port 80
- Default action: Forward to the frontend target group `aditya-mern-frontend`

Review the settings and click Create load balancer.

DNS Name Assigned: aditya-mern-frontend-329907530.us-east-1.elb.amazonaws.com

#### Backend Load Balancer

Repeat the same steps for the backend load balancer.

| Setting | Value |
|---------|-------|
| Name | aditya-mern-backend |
| Scheme | Internet-facing |
| IP address type | IPv4 |
| VPC | vpc-0929f4d11be0cef3a |
| Availability Zones | us-east-1a, us-east-1b, us-east-1c |
| Security groups | default |

Listeners and routing:
- Listener 1: Protocol HTTP, Port 80
- Default action: Forward to the backend target group `aditya-mern-backend`

Review the settings and click Create load balancer.

DNS Name Assigned: aditya-mern-backend-1715248128.us-east-1.elb.amazonaws.com

Once both are created, verify State = Active in the Load Balancers list.

Very Important Note!!! Always make sure that the node is `Healthy` and it if it is showing as `Unhealthy` then kindly check the mapping of the ports made available. Also, if the backend node is going into `Unhealthy` repeatedly, then select the Target group for backend and under Health Checks section, change the path to `/hello`. Once done, then deregister and re-register the EC2 instances, this will change the status to `Healthy` 

To verify that the deployed application is reachable through the load balancer DNS endpoints, access the URLs below:

Frontend: http://aditya-mern-frontend-329907530.us-east-1.elb.amazonaws.com

Backend: http://aditya-mern-backend-1715248128.us-east-1.elb.amazonaws.com

## Task 6 — Domain Setup with Cloudflare

Cloudflare DNS helps map your custom domain to the AWS load balancers so users can access the application using friendly names instead of long AWS-generated URLs.

### 6.1 Set Up a Domain with Namecheap and Configure Cloudflare

This step explains how to buy and configure a domain using Namecheap and then connect it to your AWS deployment.

#### Step 1: Create or Sign In to a Namecheap Account

1. Open the Namecheap website: https://www.namecheap.com/
2. Click Sign Up if you do not already have an account.
3. Create an account using your email address and a strong password.
4. Verify your email address if Namecheap asks you to confirm it.
5. Sign in to your Namecheap account.

Why this matters:
- Namecheap is the domain registrar where you can purchase and manage your domain.
- Once the domain is purchased, you can manage its DNS settings and connect it to Cloudflare.

#### Step 2: Purchase a Domain Name

1. In the Namecheap dashboard, search for a domain name you want to use.
2. Choose an available domain such as `adityabhagvathdevops.site` or any other name that suits your project.
3. Add the domain to the cart and complete the purchase.
4. Once the purchase is successful, the domain will appear in your Namecheap dashboard.

Example:
- `travelmemory.adityabhagvathdevops.site`
- `mytravelapp.xyz`

#### Step 3: Access the Domain's DNS Management Page

1. Go to the Namecheap dashboard.
2. Click on your purchased domain.
3. Open the Domain List or Manage section.
4. Find and click the option for DNS Settings, Advanced DNS, or Domain Management.

At this point, you will see the DNS records currently configured for your domain.

#### Step 4: Change the DNS to Cloudflare

Cloudflare is used to provide DNS management, security, CDN, and SSL features for your domain.

1. Go to Cloudflare and create an account if you do not already have one.
2. Add your domain to Cloudflare.
3. Cloudflare will provide you with nameservers.
4. In Namecheap, replace the existing nameservers with the Cloudflare nameservers.
5. Save the changes.

Typical Cloudflare nameservers look like this:
- `maya.ns.cloudflare.com`
- `jason.ns.cloudflare.com`

Important:
- DNS changes may take some time to propagate across the internet.
- This process can take from a few minutes to up to 24 hours.

#### Step 5: Add the DNS Records in Cloudflare

After the nameservers are updated, go to the Cloudflare dashboard and add your DNS records.

Follow the steps described in section 6.2:
- Create a CNAME record for the frontend domain.
- Create a CNAME record for the backend domain.
- Point them to the appropriate AWS Application Load Balancer DNS names.

These records tell the internet where your frontend and backend should be routed.

#### Step 6: Enable SSL/TLS in Cloudflare

To make your website secure:

1. Open the SSL/TLS section in Cloudflare.
2. Choose Full or Full (Strict) mode.
3. Make sure your AWS load balancer or EC2 instance is configured to support HTTPS properly.

This ensures that visitors can access the application securely using HTTPS.

#### Step 7: Enable Security and Performance Features

Cloudflare also adds protection and speed improvements:

- Turn on DDoS protection.
- Enable the Web Application Firewall (WAF) if needed.
- Enable caching for better performance.
- Use Cloudflare's CDN features to improve global delivery speeds.

These settings make the application safer and faster for end users.

#### Step 8: Test the Setup

After the DNS propagation completes:

1. Open your frontend domain in the browser.
2. Check whether the application loads successfully.
3. Open the backend subdomain and verify that it responds correctly.
4. Confirm that HTTPS works without certificate errors.

If something does not work, wait a little longer for DNS propagation and recheck the records.

By completing these steps, you will successfully connect your Namecheap domain to Cloudflare and point it to your AWS deployment.

### 6.2 Add DNS Records in Cloudflare

1. Log in to Cloudflare.
2. Select your domain, such as `travelmemory.adityabhagvathdevops.site`.
3. Open the DNS section.
4. Add the following CNAME records:

| Type | Name | Content (Target) | Proxy Status |
|------|------|-------------------|--------------|
| CNAME | travelmemory | aditya-mern-frontend-329907530.us-east-1.elb.amazonaws.com | Proxied |
| CNAME | back | aditya-mern-backend-1715248128.us-east-1.elb.amazonaws.com | Proxied |

What this does:
- `travelmemory.adityabhagvathdevops.site` points to the frontend load balancer, so users can access the frontend through the custom domain.
- `back.adityabhagvathdevops.site` points to the backend load balancer, so API traffic can be routed through a friendly backend subdomain.

This setup makes the application easier to access and more professional for end users.

### 6.3 Update Frontend url.js to Use the Domain

Now that the backend has a proper domain, update both frontend instances to use it instead of a raw IP address.

#### On aditya_mern_frontend

```bash
ssh -i aditya-RSA-key-AWS.pem ubuntu@10.0.2.60
cd /home/ubuntu/TravelMemory/frontend
sudo nano src/url.js
```

Change the value to:

```javascript
export const baseUrl = "http://back.adityabhagvathdevops.site"
```

#### On aditya_mern_frontend2

```bash
ssh -i aditya-RSA-key-AWS.pem ubuntu@10.0.2.61
cd /home/ubuntu/TravelMemory/frontend
sudo nano src/url.js
```

Change the value to:

```javascript
export const baseUrl = "http://back.adityabhagvathdevops.site"
```

Why use the domain instead of an IP?

If you ever change backend servers or scale to more instances, you only need to update the load balancer configuration. The domain stays the same, and the frontend does not need to be changed. This is the power of DNS abstraction.

## Optional Upgrade — Move to HTTPS with ALB and Cloudflare SSL

If you want to make the deployment more production-ready, you can upgrade the setup from HTTP to HTTPS.

### 1. Create New Target Groups for HTTPS

Create a new target group for the frontend and another for the backend, but this time configure them to support HTTPS traffic.

1. Go to AWS Console → EC2 → Target Groups → Create target group.
2. Create one target group for the frontend instances and one for the backend instances.
3. Set the protocol to `HTTPS` and the port to `443`.
4. Choose the correct VPC and register the relevant EC2 instances.
5. For the backend target group, use the health check path `/hello` so the ALB can verify that the backend is up.

This ensures the load balancer can forward secure traffic to the correct servers.

### 2. Create New Load Balancers for HTTPS

Now create new Application Load Balancers that listen on port `443`.

1. Go to AWS Console → EC2 → Load Balancers → Create Load Balancer → Application Load Balancer.
2. Create one load balancer for the frontend and one for the backend.
3. Set the listener to `HTTPS` on port `443`.
4. Forward the HTTPS listener to the appropriate target group.
5. Attach an SSL/TLS certificate from AWS Certificate Manager (ACM) or another trusted certificate source.

This allows users to access the application securely through HTTPS instead of plain HTTP.

### 3. Register EC2 Instances and Configure Backend Health Checks

After creating the target groups and load balancers:

1. Register the frontend EC2 instances to the frontend target group.
2. Register the backend EC2 instances to the backend target group.
3. Make sure the backend target group health check path is set to `/hello`.
4. Verify that all targets become `Healthy`.

If any target remains unhealthy, check the security group rules, listener configuration, and whether the backend application is responding on the correct port.

### 4. Configure SSL in Cloudflare and Update the Backend URL

Once the HTTPS load balancers are working:

1. In Cloudflare, enable SSL/TLS for your domain.
2. Make sure the DNS records point to the new HTTPS load balancer endpoints.
3. Set the SSL mode to `Full` or `Full (Strict)` for secure communication.
4. Update the frontend configuration in `src/url.js` to use HTTPS instead of HTTP.

Example:

```javascript
export const baseUrl = "https://back.adityabhagvathdevops.site"
```

After updating the URL, restart the frontend service or refresh the deployment so the new backend endpoint is used.

## Final Summary — End-to-End Deployment Flow

If the DNS records are correctly configured and all services are healthy, your 3-tier deployment is fully working.

### Full Data Flow Summary

Here is what happens when a user submits a travel memory on `travelmemory.adityabhagvathdevops.site`:

1. The user visits `http://travelmemory.adityabhagvathdevops.site` in the browser.
2. Cloudflare DNS resolves the domain to the frontend load balancer.
3. The frontend load balancer sends the request to a healthy frontend EC2 instance.
4. The React application loads in the browser.
5. The user fills the form and clicks Submit.
6. React sends a POST request to `http://back.adityabhagvathdevops.site/api/trips`.
7. Cloudflare DNS resolves the backend domain to the backend load balancer.
8. The backend load balancer routes the request to a healthy backend EC2 instance.
9. Node.js, running on port 3000 and exposed through Nginx on port 80, processes the request.
10. Node.js connects to MongoDB Atlas using the `MONGO_URI` stored in the `.env` file.
11. The trip data is saved in the `travelmemory.tripdetails` collection.
12. Node.js returns a `200 OK` response.
13. React displays the updated list of trips to the user.

### Key Concepts Quick Reference

| Term | Simple Meaning |
|------|----------------|
| EC2 Instance | A rented virtual computer running in an AWS data center |
| AMI | A snapshot or template of a configured server |
| Nginx | A lightweight web server that acts as a reverse proxy |
| Reverse Proxy | Nginx listens on port 80 and forwards traffic to Node.js on port 3000 |
| Target Group | A group of EC2 instances that a load balancer can route traffic to |
| Application Load Balancer (ALB) | Distributes HTTP requests across multiple servers intelligently |
| CNAME Record | A DNS alias that maps a domain name to an AWS load balancer DNS name |
| MongoDB Atlas | A managed cloud MongoDB database |
| `.env` file | A configuration file that stores database credentials and port values |
| `npm install` | Downloads the dependencies listed in `package.json` |
| 3-Tier Architecture | Frontend, backend, and database as separate layers |

### Ports Reference

| Layer | Technology | Port | Exposed Via |
|------|------------|------|-------------|
| Frontend | React (`npm start`) | 3000 | Nginx → port 80 |
| Backend | Node.js | 3000 | Nginx → port 80 |
| Database | MongoDB Atlas | 27017 (internal) | Accessed via MongoDB URI |
| Load Balancer | ALB Listener | 80 | Public internet |
| Cloudflare | DNS / Proxy | 80 / 443 | `travelmemory.adityabhagvathdevops.site` |

## Scope

- Provision and configure EC2 instances
- Set up backend and frontend runtime environments
- Configure environment variables in the backend
- Deploy and verify the application

## Repository

- GitHub: https://github.com/UnpredictablePrashant/TravelMemory
