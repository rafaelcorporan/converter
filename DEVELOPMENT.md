# Development Workflow Guidelines

## Overview

This document outlines the development workflow, standards, and best practices for the Video Converter project to prevent configuration inconsistencies and ensure system reliability.

## 🔧 Configuration Management

### Centralized Configuration Principle

**RULE**: All service configurations MUST be managed through the centralized configuration system.

```
config.json → Single source of truth
    ↓
api/config.py → Python configuration manager
    ↓
Environment variables → Runtime overrides
```

### Configuration Modification Process

1. **Update `config.json`** - Make changes to the central configuration
2. **Validate Changes** - Run `python3 scripts/validate_config.py`
3. **Test Integration** - Run `python3 tests/test_integration.py`
4. **Update Documentation** - Reflect changes in README.md if needed

### Environment Variables

- **Development**: Use `.env` for local overrides
- **Production**: Set environment variables directly
- **Never commit** `.env` files to the repository

## 🔍 Pre-Commit Checklist

Before committing any changes, ensure:

### Configuration Consistency
```bash
# Validate configuration
python3 scripts/validate_config.py

# Run integration tests
python3 tests/test_integration.py

# Check port consistency
grep -r "5001" . --include="*.py" --include="*.ts" --include="*.js" --include="*.md"
```

### Code Quality
- [ ] All Python files pass syntax validation
- [ ] TypeScript/JavaScript files compile without errors
- [ ] No hardcoded port numbers outside of configuration
- [ ] Configuration changes are reflected across all relevant files

### Testing Requirements
- [ ] Integration tests pass
- [ ] Backend health check responds correctly
- [ ] Frontend can connect to backend
- [ ] All API endpoints are accessible

## 🚀 Development Workflow

### 1. Setting Up Development Environment

```bash
# Clone and setup
git clone <repository-url>
cd project

# Install dependencies
npm install
cd api && pip install -r requirements.txt && cd ..

# Copy environment template
cp .env.example .env

# Validate configuration
python3 scripts/validate_config.py

# Start development servers
./start-unified.sh
```

### 2. Making Changes

#### Backend Changes
1. **Use Unified Backend**: Always use `unified_video_converter.py`
2. **Configuration**: Import from `api.config` module
3. **Testing**: Validate with health checks
4. **Logging**: Use proper logging levels

#### Frontend Changes
1. **API Integration**: Use `lib/video-api.ts` for backend communication
2. **Configuration**: Respect environment variables
3. **Error Handling**: Handle connection failures gracefully

#### Configuration Changes
1. **Update `config.json`** first
2. **Run validation** scripts
3. **Update environment** template if needed
4. **Test all affected** components

### 3. Testing Process

#### Local Testing
```bash
# Configuration validation
python3 scripts/validate_config.py

# Integration testing
python3 tests/test_integration.py

# Health monitoring (optional)
python3 monitor/health_monitor.py
```

#### Manual Testing
1. Start both services with `./start-unified.sh`
2. Verify frontend loads at `http://localhost:3000`
3. Test video upload and conversion workflow
4. Check health endpoint: `curl http://localhost:5001/api/health`

## 📋 Code Review Standards

### Configuration Review Checklist

When reviewing code that affects configuration:

- [ ] **Port Consistency**: All port references use the same value
- [ ] **Environment Support**: New configuration supports environment overrides
- [ ] **Validation**: Configuration validation scripts updated if needed
- [ ] **Documentation**: Changes reflected in README.md
- [ ] **Testing**: Integration tests cover new configuration

### Backend Review Checklist

- [ ] **Unified Backend**: Changes use `unified_video_converter.py`
- [ ] **Configuration Import**: Uses `config` module for settings
- [ ] **Error Handling**: Proper error responses and logging
- [ ] **Health Endpoint**: Health check reflects service state
- [ ] **Dependencies**: No new hardcoded configuration values

### Frontend Review Checklist

- [ ] **API Integration**: Uses `lib/video-api.ts` for backend calls
- [ ] **Error Handling**: Graceful handling of connection failures
- [ ] **Environment Variables**: Respects `NEXT_PUBLIC_API_URL`
- [ ] **Type Safety**: TypeScript types updated if needed

## 🛠️ Common Development Tasks

### Adding New Configuration

1. **Add to `config.json`**:
```json
{
  "new_section": {
    "new_setting": "default_value"
  }
}
```

2. **Update `api/config.py`** if needed:
```python
def get_new_section_config(self) -> Dict[str, Any]:
    return self._config.get('new_section', {})
```

3. **Add environment variable support**:
```python
if os.getenv('NEW_SETTING'):
    self._config['new_section']['new_setting'] = os.getenv('NEW_SETTING')
```

4. **Update `.env.example`**:
```bash
# New Configuration Section
NEW_SETTING=default_value
```

5. **Validate**:
```bash
python3 scripts/validate_config.py
```

### Adding New API Endpoint

1. **Backend** (`api/unified_video_converter.py`):
```python
@app.route('/api/new-endpoint', methods=['GET'])
def new_endpoint():
    return jsonify({'message': 'New endpoint'})
```

2. **Frontend** (`lib/video-api.ts`):
```typescript
static async newEndpoint(): Promise<ResponseType> {
  return this.makeRequest<ResponseType>('/api/new-endpoint')
}
```

3. **Test Integration**:
```bash
python3 tests/test_integration.py
```

### Debugging Connection Issues

1. **Check Configuration**:
```bash
python3 scripts/validate_config.py
```

2. **Verify Backend Health**:
```bash
curl http://localhost:5001/api/health
```

3. **Check Port Binding**:
```bash
lsof -i :5001
```

4. **Monitor Health**:
```bash
python3 monitor/health_monitor.py
```

## 🚨 Incident Response

### Connection Failure Resolution

1. **Immediate Actions**:
   - Check if backend is running: `curl http://localhost:5001/api/health`
   - Verify port configuration: `python3 scripts/validate_config.py`
   - Restart services: `./start-unified.sh`

2. **Investigation**:
   - Check logs: `tail -f logs/health_monitor.log`
   - Validate configuration: `python3 scripts/validate_config.py`
   - Run integration tests: `python3 tests/test_integration.py`

3. **Root Cause Analysis**:
   - Port configuration inconsistency
   - Service startup failure
   - Environment variable mismatch
   - Network connectivity issues

### Configuration Drift Prevention

1. **Use Pre-commit Hooks**:
```bash
# Setup pre-commit validation
ln -s ../../scripts/pre-commit-check.sh .git/hooks/pre-commit
```

2. **Regular Validation**:
```bash
# Daily configuration check
python3 scripts/validate_config.py
```

3. **Monitoring**:
```bash
# Continuous health monitoring
python3 monitor/health_monitor.py
```

## 📚 Best Practices

### Configuration Management
- ✅ Always use centralized configuration (`config.json`)
- ✅ Support environment variable overrides
- ✅ Validate configuration before committing
- ❌ Never hardcode ports or URLs in source code
- ❌ Never commit `.env` files

### Service Integration
- ✅ Use health checks for service validation
- ✅ Implement proper error handling for connection failures
- ✅ Test integration after configuration changes
- ❌ Assume services are always available
- ❌ Skip validation steps

### Development Process
- ✅ Run validation scripts before committing
- ✅ Test locally before pushing changes
- ✅ Update documentation with configuration changes
- ❌ Make configuration changes without validation
- ❌ Skip integration testing

## 🔗 Quick Reference

### Essential Commands
```bash
# Validate everything
python3 scripts/validate_config.py

# Test integration
python3 tests/test_integration.py

# Start services
./start-unified.sh

# Monitor health
python3 monitor/health_monitor.py

# Check connectivity
curl http://localhost:5001/api/health
```

### Key Files
- `config.json` - Central configuration
- `api/config.py` - Configuration manager
- `.env.example` - Environment template
- `scripts/validate_config.py` - Validation script
- `tests/test_integration.py` - Integration tests
- `monitor/health_monitor.py` - Health monitoring

### Port Configuration
- **Frontend**: 3000 (Next.js)
- **Backend**: 5001 (Flask API)
- **Configuration**: `config.json` → `services.backend.port`
- **Environment**: `BACKEND_PORT`, `NEXT_PUBLIC_API_URL`

---

*This workflow ensures the "CANNOT CONNECT TO VIDEO CONVERSION SERVER" error and similar configuration-related issues are prevented through systematic configuration management and validation.*