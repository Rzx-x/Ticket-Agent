-- Database initialization script for OmniDesk AI
-- This script sets up the initial database structure and configurations

-- Create database if it doesn't exist (handled by docker-compose)
-- Ensure we're using the correct database
\\c omnidesk;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";
CREATE EXTENSION IF NOT EXISTS \"pg_trgm\";  -- For text search
CREATE EXTENSION IF NOT EXISTS \"unaccent\"; -- For accent-insensitive search

-- Create custom types for ticket status and urgency
DO $$ BEGIN
    CREATE TYPE ticket_source AS ENUM ('email', 'sms', 'glpi', 'solman', 'web', 'phone');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE ticket_urgency AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE ticket_status AS ENUM ('open', 'in_progress', 'pending', 'resolved', 'closed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE interaction_type AS ENUM ('user_message', 'ai_response', 'agent_response', 'system_note', 'email_sent', 'sms_sent');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create function to generate ticket numbers
CREATE OR REPLACE FUNCTION generate_ticket_number()
RETURNS TEXT AS $$
DECLARE
    ticket_num TEXT;
    counter INTEGER;
BEGIN
    -- Get current date in format YYYYMMDD
    ticket_num := 'TKT-' || TO_CHAR(CURRENT_DATE, 'YYYYMMDD') || '-';
    
    -- Get next sequence number for today
    SELECT COALESCE(MAX(CAST(SUBSTRING(ticket_number FROM LENGTH(ticket_num) + 1) AS INTEGER)), 0) + 1
    INTO counter
    FROM tickets
    WHERE ticket_number LIKE ticket_num || '%';
    
    -- Return formatted ticket number
    RETURN ticket_num || LPAD(counter::TEXT, 4, '0');
END;
$$ LANGUAGE plpgsql;

-- Insert initial configuration data
INSERT INTO public.knowledge_articles (id, title, content, category, tags, language, is_published, author)
VALUES 
    (uuid_generate_v4(), 
     'VPN Connection Issues', 
     'Common VPN connection problems and solutions:\n\n1. Check internet connectivity\n2. Verify VPN credentials\n3. Try different VPN servers\n4. Restart VPN client\n5. Check firewall settings\n\nFor persistent issues, contact IT support.',
     'Network',
     'vpn,connection,network,troubleshooting',
     'en',
     true,
     'System')
ON CONFLICT DO NOTHING;

INSERT INTO public.knowledge_articles (id, title, content, category, tags, language, is_published, author)
VALUES 
    (uuid_generate_v4(),
     'Email Configuration Problems',
     'Email setup and configuration guide:\n\n1. Verify email server settings\n2. Check authentication credentials\n3. Test port connectivity\n4. Configure security settings\n5. Import certificates if required\n\nCommon email servers:\n- Exchange: Usually port 993 (IMAP) or 995 (POP3)\n- Gmail: IMAP port 993, SMTP port 587',
     'Email',
     'email,outlook,configuration,smtp,imap',
     'en',
     true,
     'System')
ON CONFLICT DO NOTHING;

INSERT INTO public.knowledge_articles (id, title, content, category, tags, language, is_published, author)
VALUES 
    (uuid_generate_v4(),
     'Password Reset Procedure',
     'Password reset steps:\n\n1. Visit company password reset portal\n2. Enter your employee ID or email\n3. Answer security questions\n4. Check email for reset link\n5. Create new strong password\n\nPassword requirements:\n- Minimum 8 characters\n- Include uppercase, lowercase, numbers\n- Include special characters\n- Cannot reuse last 5 passwords',
     'Account',
     'password,reset,security,account',
     'en',
     true,
     'System')
ON CONFLICT DO NOTHING;

-- Create indexes for better performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tickets_created_at ON public.tickets USING btree (created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tickets_status ON public.tickets USING btree (status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tickets_category ON public.tickets USING btree (category);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tickets_urgency ON public.tickets USING btree (urgency);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tickets_user_email ON public.tickets USING btree (user_email);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tickets_source ON public.tickets USING btree (source);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tickets_external_id ON public.tickets USING btree (external_id);

-- Text search indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tickets_subject_gin ON public.tickets USING gin (to_tsvector('english', subject));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tickets_description_gin ON public.tickets USING gin (to_tsvector('english', description));

-- Interaction indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_interactions_ticket_id ON public.ticket_interactions USING btree (ticket_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_interactions_created_at ON public.ticket_interactions USING btree (created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_interactions_type ON public.ticket_interactions USING btree (interaction_type);

-- Knowledge base indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_kb_category ON public.knowledge_articles USING btree (category);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_kb_published ON public.knowledge_articles USING btree (is_published);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_kb_content_gin ON public.knowledge_articles USING gin (to_tsvector('english', title || ' ' || content));

-- Create a view for ticket statistics
CREATE OR REPLACE VIEW ticket_statistics AS
SELECT 
    COUNT(*) as total_tickets,
    COUNT(*) FILTER (WHERE status = 'open') as open_tickets,
    COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress_tickets,
    COUNT(*) FILTER (WHERE status = 'resolved') as resolved_tickets,
    COUNT(*) FILTER (WHERE status = 'closed') as closed_tickets,
    AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))/3600) FILTER (WHERE resolved_at IS NOT NULL) as avg_resolution_hours,
    COUNT(*) FILTER (WHERE ai_processed = true) as ai_processed_count,
    (COUNT(*) FILTER (WHERE ai_processed = true)::float / COUNT(*) * 100) as ai_processing_rate
FROM tickets;

-- Create a view for daily ticket trends
CREATE OR REPLACE VIEW daily_ticket_trends AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as tickets_created,
    COUNT(*) FILTER (WHERE status IN ('resolved', 'closed')) as tickets_resolved,
    AVG(priority) as avg_priority
FROM tickets
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Insert sample tickets for testing (only in development)
INSERT INTO public.tickets (
    id, ticket_number, source, user_email, user_name, 
    subject, description, language, category, urgency, 
    priority, status, ai_processed
)
VALUES 
    (uuid_generate_v4(), generate_ticket_number(), 'web', 'john.doe@powergrid.com', 'John Doe',
     'VPN Connection Issues', 'I am unable to connect to the company VPN from my home network. Getting connection timeout errors.',
     'en', 'Network', 'high', 3, 'open', false),
    (uuid_generate_v4(), generate_ticket_number(), 'email', 'priya.sharma@powergrid.com', 'Priya Sharma',
     'Email nahi aa raha hai', 'Mera Outlook mein emails receive nahi ho rahe hain. Please help karo.',
     'hi', 'Email', 'medium', 2, 'in_progress', true),
    (uuid_generate_v4(), generate_ticket_number(), 'glpi', 'rajesh.kumar@powergrid.com', 'Rajesh Kumar',
     'Printer not working', 'Office printer is showing paper jam error but there is no paper stuck.',
     'en', 'Printer', 'low', 1, 'resolved', true)
ON CONFLICT DO NOTHING;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE omnidesk TO omnidesk;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO omnidesk;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO omnidesk;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO omnidesk;

-- Create application user for API access
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'omnidesk_api') THEN
        CREATE USER omnidesk_api WITH ENCRYPTED PASSWORD 'api_secure_password';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE omnidesk TO omnidesk_api;
GRANT USAGE ON SCHEMA public TO omnidesk_api;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO omnidesk_api;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO omnidesk_api;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO omnidesk_api;

-- Show completion message
SELECT 'Database initialization completed successfully!' as status;