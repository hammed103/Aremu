#!/usr/bin/env node
/**
 * Baileys WhatsApp Scraper CLI
 * Command line interface for managing the WhatsApp scraper
 */

const BaileysWhatsAppScraper = require('./index.js');
const fs = require('fs');
const path = require('path');

class BaileysScraperCLI {
    constructor() {
        this.scraper = new BaileysWhatsAppScraper();
        this.commands = {
            'start': this.startScraper.bind(this),
            'stop': this.stopScraper.bind(this),
            'stats': this.showStats.bind(this),
            'report': this.generateReport.bind(this),
            'help': this.showHelp.bind(this)
        };
    }
    
    async startScraper() {
        console.log('🚀 Starting WhatsApp scraper...');
        try {
            await this.scraper.start();
            console.log('✅ Scraper started successfully!');
            console.log('📱 Scan the QR code with your WhatsApp to connect');
            console.log('💡 Press Ctrl+C to stop');
            
            // Keep the process alive
            process.stdin.resume();
            
        } catch (error) {
            console.error('❌ Failed to start scraper:', error.message);
            process.exit(1);
        }
    }
    
    async stopScraper() {
        console.log('🛑 Stopping WhatsApp scraper...');
        try {
            await this.scraper.stop();
            console.log('✅ Scraper stopped successfully!');
        } catch (error) {
            console.error('❌ Error stopping scraper:', error.message);
        }
    }
    
    async showStats() {
        console.log('📊 Getting scraper statistics...');
        try {
            const stats = await this.scraper.getStats();
            
            console.log('\n' + '='.repeat(40));
            console.log('📈 BAILEYS WHATSAPP SCRAPER STATS');
            console.log('='.repeat(40));
            console.log(`📱 Connection Status: ${stats.connected ? '✅ Connected' : '❌ Disconnected'}`);
            console.log(`💼 Total Jobs Scraped: ${stats.totalJobs || 0}`);
            console.log(`🕐 Last Update: ${stats.lastUpdate ? stats.lastUpdate.toLocaleString() : 'Never'}`);
            console.log('='.repeat(40));
            
            if (stats.error) {
                console.error(`❌ Error: ${stats.error}`);
            }
            
        } catch (error) {
            console.error('❌ Failed to get stats:', error.message);
        }
    }
    
    async generateReport() {
        console.log('📋 Generating detailed report...');
        try {
            const jobsFile = path.join(__dirname, 'data', 'jobs.json');
            
            if (!fs.existsSync(jobsFile)) {
                console.log('📄 No jobs data found. Start scraping first!');
                return;
            }
            
            const jobsData = JSON.parse(fs.readFileSync(jobsFile, 'utf8'));
            
            console.log('\n' + '='.repeat(50));
            console.log('📊 DETAILED WHATSAPP SCRAPER REPORT');
            console.log('='.repeat(50));
            
            // Basic stats
            console.log(`📱 Total Messages Processed: ${jobsData.length}`);
            
            // Group by date
            const byDate = {};
            jobsData.forEach(job => {
                const date = new Date(job.timestamp).toDateString();
                byDate[date] = (byDate[date] || 0) + 1;
            });
            
            console.log('\n📅 Jobs by Date:');
            Object.entries(byDate)
                .sort(([a], [b]) => new Date(b) - new Date(a))
                .slice(0, 7) // Last 7 days
                .forEach(([date, count]) => {
                    console.log(`   ${date}: ${count} jobs`);
                });
            
            // Group by source (WhatsApp group/channel)
            const bySources = {};
            jobsData.forEach(job => {
                const source = job.from || 'Unknown';
                bySources[source] = (bySources[source] || 0) + 1;
            });
            
            console.log('\n📱 Top WhatsApp Sources:');
            Object.entries(bySources)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 10)
                .forEach(([source, count]) => {
                    const displaySource = source.includes('@') ? 
                        source.split('@')[0] : source;
                    console.log(`   ${displaySource}: ${count} jobs`);
                });
            
            // Recent jobs
            console.log('\n🕐 Recent Jobs (Last 5):');
            jobsData
                .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
                .slice(0, 5)
                .forEach((job, index) => {
                    const preview = job.text.substring(0, 100) + '...';
                    const time = new Date(job.timestamp).toLocaleString();
                    console.log(`   ${index + 1}. [${time}] ${preview}`);
                });
            
            console.log('='.repeat(50));
            
        } catch (error) {
            console.error('❌ Failed to generate report:', error.message);
        }
    }
    
    showHelp() {
        console.log('\n🔧 BAILEYS WHATSAPP SCRAPER CLI');
        console.log('='.repeat(35));
        console.log('Available commands:');
        console.log('');
        console.log('  start    🚀 Start the WhatsApp scraper');
        console.log('  stop     🛑 Stop the WhatsApp scraper');
        console.log('  stats    📊 Show scraper statistics');
        console.log('  report   📋 Generate detailed report');
        console.log('  help     ❓ Show this help message');
        console.log('');
        console.log('Examples:');
        console.log('  node cli.js start');
        console.log('  node cli.js stats');
        console.log('  npm run stats');
        console.log('  npm run report');
        console.log('');
    }
    
    async run() {
        const args = process.argv.slice(2);
        const command = args[0] || 'help';
        
        if (this.commands[command]) {
            try {
                await this.commands[command]();
            } catch (error) {
                console.error(`❌ Command failed: ${error.message}`);
                process.exit(1);
            }
        } else {
            console.error(`❌ Unknown command: ${command}`);
            this.showHelp();
            process.exit(1);
        }
    }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
    console.log('\n👋 Goodbye!');
    process.exit(0);
});

// Run CLI if called directly
if (require.main === module) {
    const cli = new BaileysScraperCLI();
    cli.run();
}

module.exports = BaileysScraperCLI;
