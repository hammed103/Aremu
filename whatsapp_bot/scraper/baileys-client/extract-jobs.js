#!/usr/bin/env node
/**
 * Job Extraction Utility for Baileys WhatsApp Scraper
 * Processes and extracts job data from WhatsApp messages
 */

const fs = require('fs');
const path = require('path');
const { Client } = require('pg');

class JobExtractor {
    constructor() {
        this.dataDir = path.join(__dirname, 'data');
        this.jobsFile = path.join(this.dataDir, 'jobs.json');
        this.dbConfig = {
            connectionString: process.env.DATABASE_URL || 
                "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        };
    }
    
    async extractAll() {
        console.log('🔍 Extracting all job data...');
        
        if (!fs.existsSync(this.jobsFile)) {
            console.log('📄 No jobs file found. Run the scraper first!');
            return;
        }
        
        try {
            const jobsData = JSON.parse(fs.readFileSync(this.jobsFile, 'utf8'));
            console.log(`📊 Found ${jobsData.length} job messages`);
            
            // Process and enhance job data
            const processedJobs = jobsData.map(job => this.enhanceJobData(job));
            
            // Save enhanced data
            const enhancedFile = path.join(this.dataDir, 'enhanced-jobs.json');
            fs.writeFileSync(enhancedFile, JSON.stringify(processedJobs, null, 2));
            
            console.log(`✅ Enhanced job data saved to: ${enhancedFile}`);
            console.log(`📈 Processed ${processedJobs.length} jobs`);
            
            return processedJobs;
            
        } catch (error) {
            console.error('❌ Error extracting jobs:', error.message);
        }
    }
    
    enhanceJobData(job) {
        const text = job.text.toLowerCase();
        
        // Extract potential job title
        const titleKeywords = ['developer', 'engineer', 'manager', 'analyst', 'coordinator', 'specialist', 'assistant'];
        let title = 'Job Opportunity';
        
        for (const keyword of titleKeywords) {
            if (text.includes(keyword)) {
                title = keyword.charAt(0).toUpperCase() + keyword.slice(1);
                break;
            }
        }
        
        // Extract location
        const locationKeywords = ['lagos', 'abuja', 'kano', 'port harcourt', 'ibadan', 'remote'];
        let location = 'Nigeria';
        
        for (const loc of locationKeywords) {
            if (text.includes(loc)) {
                location = loc.charAt(0).toUpperCase() + loc.slice(1);
                break;
            }
        }
        
        // Extract salary info
        const salaryMatch = text.match(/(\d+[,\d]*)\s*(naira|₦|k|million)/i);
        let salary = null;
        if (salaryMatch) {
            salary = salaryMatch[0];
        }
        
        // Determine job type
        let jobType = 'Full-time';
        if (text.includes('remote') || text.includes('work from home')) {
            jobType = 'Remote';
        } else if (text.includes('part-time')) {
            jobType = 'Part-time';
        } else if (text.includes('contract') || text.includes('freelance')) {
            jobType = 'Contract';
        } else if (text.includes('internship')) {
            jobType = 'Internship';
        }
        
        return {
            ...job,
            enhanced: {
                title,
                location,
                salary,
                jobType,
                extractedAt: new Date().toISOString()
            }
        };
    }
    
    async showStats() {
        console.log('📊 Job extraction statistics...');
        
        if (!fs.existsSync(this.jobsFile)) {
            console.log('📄 No jobs data found.');
            return;
        }
        
        try {
            const jobsData = JSON.parse(fs.readFileSync(this.jobsFile, 'utf8'));
            
            console.log('\n' + '='.repeat(40));
            console.log('📈 JOB EXTRACTION STATS');
            console.log('='.repeat(40));
            console.log(`📱 Total Messages: ${jobsData.length}`);
            
            // Analyze by keywords
            const keywordStats = {};
            const keywords = ['developer', 'engineer', 'manager', 'remote', 'lagos', 'abuja'];
            
            keywords.forEach(keyword => {
                const count = jobsData.filter(job => 
                    job.text.toLowerCase().includes(keyword)
                ).length;
                keywordStats[keyword] = count;
            });
            
            console.log('\n🔍 Keyword Analysis:');
            Object.entries(keywordStats).forEach(([keyword, count]) => {
                console.log(`   ${keyword}: ${count} mentions`);
            });
            
            // Recent activity
            const recent = jobsData.filter(job => {
                const jobDate = new Date(job.timestamp);
                const dayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
                return jobDate > dayAgo;
            });
            
            console.log(`\n🕐 Last 24 hours: ${recent.length} new jobs`);
            console.log('='.repeat(40));
            
        } catch (error) {
            console.error('❌ Error showing stats:', error.message);
        }
    }
    
    async searchJobs(query) {
        console.log(`🔍 Searching for: "${query}"`);
        
        if (!fs.existsSync(this.jobsFile)) {
            console.log('📄 No jobs data found.');
            return;
        }
        
        try {
            const jobsData = JSON.parse(fs.readFileSync(this.jobsFile, 'utf8'));
            const searchTerm = query.toLowerCase();
            
            const results = jobsData.filter(job => 
                job.text.toLowerCase().includes(searchTerm)
            );
            
            console.log(`\n📊 Found ${results.length} matching jobs:`);
            console.log('='.repeat(50));
            
            results.slice(0, 10).forEach((job, index) => {
                const preview = job.text.substring(0, 150) + '...';
                const time = new Date(job.timestamp).toLocaleString();
                console.log(`\n${index + 1}. [${time}]`);
                console.log(`   ${preview}`);
            });
            
            if (results.length > 10) {
                console.log(`\n... and ${results.length - 10} more results`);
            }
            
        } catch (error) {
            console.error('❌ Error searching jobs:', error.message);
        }
    }
    
    async exportToDatabase() {
        console.log('💾 Exporting jobs to database...');
        
        if (!fs.existsSync(this.jobsFile)) {
            console.log('📄 No jobs data found.');
            return;
        }
        
        const client = new Client(this.dbConfig);
        
        try {
            await client.connect();
            const jobsData = JSON.parse(fs.readFileSync(this.jobsFile, 'utf8'));
            
            let exported = 0;
            let skipped = 0;
            
            for (const job of jobsData) {
                try {
                    const enhanced = this.enhanceJobData(job);
                    
                    const query = `
                        INSERT INTO raw_jobs (
                            external_id, source, title, company, location, 
                            description, posted_date, scraped_at, raw_data
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (external_id, source) DO NOTHING
                    `;
                    
                    const values = [
                        job.id,
                        'whatsapp',
                        enhanced.enhanced.title,
                        'WhatsApp Group',
                        enhanced.enhanced.location,
                        job.text,
                        new Date(job.timestamp),
                        new Date(),
                        JSON.stringify(enhanced)
                    ];
                    
                    const result = await client.query(query, values);
                    if (result.rowCount > 0) {
                        exported++;
                    } else {
                        skipped++;
                    }
                    
                } catch (error) {
                    console.error(`❌ Error exporting job ${job.id}:`, error.message);
                    skipped++;
                }
            }
            
            console.log(`✅ Export complete:`);
            console.log(`   📈 Exported: ${exported} jobs`);
            console.log(`   ⏭️ Skipped: ${skipped} jobs (duplicates)`);
            
        } catch (error) {
            console.error('❌ Database export failed:', error.message);
        } finally {
            await client.end();
        }
    }
    
    async run() {
        const args = process.argv.slice(2);
        const command = args[0] || 'help';
        
        switch (command) {
            case 'extract':
                if (args[1] === '--all') {
                    await this.extractAll();
                } else {
                    console.log('Usage: extract --all');
                }
                break;
                
            case 'stats':
                await this.showStats();
                break;
                
            case 'search':
                const query = args.slice(1).join(' ');
                if (query) {
                    await this.searchJobs(query);
                } else {
                    console.log('Usage: search <query>');
                }
                break;
                
            case 'export':
                await this.exportToDatabase();
                break;
                
            default:
                console.log('\n🔧 JOB EXTRACTOR CLI');
                console.log('='.repeat(25));
                console.log('Commands:');
                console.log('  extract --all    Extract and enhance all job data');
                console.log('  stats           Show extraction statistics');
                console.log('  search <query>  Search for specific jobs');
                console.log('  export          Export jobs to database');
                console.log('');
                console.log('Examples:');
                console.log('  node extract-jobs.js extract --all');
                console.log('  node extract-jobs.js search developer');
                console.log('  npm run jobs-stats');
                break;
        }
    }
}

if (require.main === module) {
    const extractor = new JobExtractor();
    extractor.run();
}

module.exports = JobExtractor;
