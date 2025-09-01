#!/usr/bin/env node
/**
 * Baileys WhatsApp Client - Main Entry Point
 * Connects to WhatsApp and scrapes job postings from groups/channels
 */

const { default: makeWASocket, DisconnectReason, useMultiFileAuthState } = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const path = require('path');
const { Client } = require('pg');

class BaileysWhatsAppScraper {
    constructor() {
        this.sock = null;
        this.isConnected = false;
        this.authDir = path.join(__dirname, 'auth');
        this.dataDir = path.join(__dirname, 'data');
        this.jobsFile = path.join(this.dataDir, 'jobs.json');
        
        // Database configuration
        this.dbConfig = {
            connectionString: process.env.DATABASE_URL || 
                "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        };
        
        // Job keywords to look for
        this.jobKeywords = [
            'job', 'hiring', 'vacancy', 'position', 'opportunity', 'career',
            'developer', 'engineer', 'analyst', 'manager', 'coordinator',
            'remote', 'work from home', 'freelance', 'contract', 'full-time',
            'part-time', 'internship', 'graduate', 'entry level', 'senior',
            'lagos', 'abuja', 'nigeria', 'naira', 'salary', 'cv', 'resume'
        ];
        
        this.ensureDirectories();
    }
    
    ensureDirectories() {
        if (!fs.existsSync(this.authDir)) {
            fs.mkdirSync(this.authDir, { recursive: true });
        }
        if (!fs.existsSync(this.dataDir)) {
            fs.mkdirSync(this.dataDir, { recursive: true });
        }
    }
    
    async connectToWhatsApp() {
        try {
            console.log('🔄 Initializing WhatsApp connection...');
            
            const { state, saveCreds } = await useMultiFileAuthState(this.authDir);
            
            this.sock = makeWASocket({
                auth: state,
                printQRInTerminal: true,
                logger: {
                    level: 'silent',
                    child: () => ({ level: 'silent' })
                }
            });
            
            this.sock.ev.on('creds.update', saveCreds);
            
            this.sock.ev.on('connection.update', (update) => {
                const { connection, lastDisconnect, qr } = update;
                
                if (qr) {
                    console.log('📱 Scan QR code with WhatsApp:');
                    qrcode.generate(qr, { small: true });
                }
                
                if (connection === 'close') {
                    const shouldReconnect = (lastDisconnect?.error instanceof Boom) &&
                        lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
                    
                    console.log('❌ Connection closed due to:', lastDisconnect?.error);
                    
                    if (shouldReconnect) {
                        console.log('🔄 Reconnecting...');
                        this.connectToWhatsApp();
                    }
                } else if (connection === 'open') {
                    console.log('✅ WhatsApp connected successfully!');
                    this.isConnected = true;
                    this.startMessageListener();
                }
            });
            
        } catch (error) {
            console.error('❌ Failed to connect to WhatsApp:', error);
            throw error;
        }
    }
    
    startMessageListener() {
        console.log('👂 Starting message listener for job postings...');
        
        this.sock.ev.on('messages.upsert', async (m) => {
            try {
                for (const message of m.messages) {
                    if (message.key.fromMe) continue; // Skip own messages
                    
                    const messageText = this.extractMessageText(message);
                    if (messageText && this.isJobRelated(messageText)) {
                        console.log('💼 Job-related message detected!');
                        await this.processJobMessage(message, messageText);
                    }
                }
            } catch (error) {
                console.error('❌ Error processing messages:', error);
            }
        });
    }
    
    extractMessageText(message) {
        if (message.message?.conversation) {
            return message.message.conversation;
        } else if (message.message?.extendedTextMessage?.text) {
            return message.message.extendedTextMessage.text;
        } else if (message.message?.imageMessage?.caption) {
            return message.message.imageMessage.caption;
        } else if (message.message?.documentMessage?.caption) {
            return message.message.documentMessage.caption;
        }
        return null;
    }
    
    isJobRelated(text) {
        const lowerText = text.toLowerCase();
        return this.jobKeywords.some(keyword => lowerText.includes(keyword));
    }
    
    async processJobMessage(message, messageText) {
        try {
            const jobData = {
                id: message.key.id,
                from: message.key.remoteJid,
                timestamp: new Date(message.messageTimestamp * 1000),
                text: messageText,
                source: 'whatsapp',
                raw_data: JSON.stringify(message)
            };
            
            // Save to local file
            await this.saveJobToFile(jobData);
            
            // Save to database
            await this.saveJobToDatabase(jobData);
            
            console.log(`✅ Job message saved: ${jobData.id}`);
            
        } catch (error) {
            console.error('❌ Error processing job message:', error);
        }
    }
    
    async saveJobToFile(jobData) {
        try {
            let jobs = [];
            if (fs.existsSync(this.jobsFile)) {
                const fileContent = fs.readFileSync(this.jobsFile, 'utf8');
                jobs = JSON.parse(fileContent);
            }
            
            jobs.push(jobData);
            fs.writeFileSync(this.jobsFile, JSON.stringify(jobs, null, 2));
            
        } catch (error) {
            console.error('❌ Error saving job to file:', error);
        }
    }
    
    async saveJobToDatabase(jobData) {
        const client = new Client(this.dbConfig);
        
        try {
            await client.connect();
            
            const query = `
                INSERT INTO raw_jobs (
                    external_id, source, title, company, location, 
                    description, posted_date, scraped_at, raw_data
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (external_id, source) DO NOTHING
            `;
            
            const values = [
                jobData.id,
                'whatsapp',
                'WhatsApp Job Posting', // Will be enhanced by AI parser
                'Unknown', // Will be enhanced by AI parser
                'Nigeria', // Default location
                jobData.text,
                jobData.timestamp,
                new Date(),
                jobData.raw_data
            ];
            
            await client.query(query, values);
            console.log(`💾 Job saved to database: ${jobData.id}`);
            
        } catch (error) {
            console.error('❌ Database error:', error);
        } finally {
            await client.end();
        }
    }
    
    async getStats() {
        try {
            if (fs.existsSync(this.jobsFile)) {
                const fileContent = fs.readFileSync(this.jobsFile, 'utf8');
                const jobs = JSON.parse(fileContent);
                
                console.log('📊 WhatsApp Scraper Stats:');
                console.log(`Total jobs scraped: ${jobs.length}`);
                console.log(`Connection status: ${this.isConnected ? '✅ Connected' : '❌ Disconnected'}`);
                
                return {
                    totalJobs: jobs.length,
                    connected: this.isConnected,
                    lastUpdate: new Date()
                };
            }
            
            return { totalJobs: 0, connected: this.isConnected };
            
        } catch (error) {
            console.error('❌ Error getting stats:', error);
            return { error: error.message };
        }
    }
    
    async start() {
        console.log('🚀 Starting Baileys WhatsApp Scraper...');
        await this.connectToWhatsApp();
    }
    
    async stop() {
        console.log('🛑 Stopping WhatsApp scraper...');
        if (this.sock) {
            await this.sock.logout();
        }
        this.isConnected = false;
    }
}

// Export for use as module
module.exports = BaileysWhatsAppScraper;

// Run directly if called as script
if (require.main === module) {
    const scraper = new BaileysWhatsAppScraper();
    
    process.on('SIGINT', async () => {
        console.log('\n👋 Gracefully shutting down...');
        await scraper.stop();
        process.exit(0);
    });
    
    scraper.start().catch(console.error);
}
