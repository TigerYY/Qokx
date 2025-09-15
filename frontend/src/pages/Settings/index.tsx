import React, { useState } from 'react';
import {
  Grid,
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  Chip,
} from '@mui/material';
import {
  Save,
  Refresh,
  Security,
  Notifications,
  Palette,
  Language,
} from '@mui/icons-material';

const Settings: React.FC = () => {
  const [settings, setSettings] = useState({
    // 交易设置
    defaultSymbol: 'BTC-USDT',
    defaultTimeframe: '1H',
    maxPositionSize: 0.2,
    riskLevel: 'medium',
    autoStart: false,
    
    // 风险设置
    maxDrawdown: 5.0,
    stopLoss: 2.0,
    takeProfit: 4.0,
    maxDailyLoss: 3.0,
    
    // 通知设置
    emailNotifications: true,
    pushNotifications: false,
    riskAlerts: true,
    tradeAlerts: true,
    
    // 界面设置
    theme: 'dark',
    language: 'zh',
    autoRefresh: true,
    refreshInterval: 30,
    
    // 系统设置
    logLevel: 'info',
    dataRetention: 30,
    backupEnabled: true,
  });

  const [hasChanges, setHasChanges] = useState(false);

  const handleSettingChange = (key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
    setHasChanges(true);
  };

  const handleSave = () => {
    // 保存设置到后端
    console.log('保存设置:', settings);
    setHasChanges(false);
  };

  const handleReset = () => {
    // 重置为默认设置
    setSettings({
      defaultSymbol: 'BTC-USDT',
      defaultTimeframe: '1H',
      maxPositionSize: 0.2,
      riskLevel: 'medium',
      autoStart: false,
      maxDrawdown: 5.0,
      stopLoss: 2.0,
      takeProfit: 4.0,
      maxDailyLoss: 3.0,
      emailNotifications: true,
      pushNotifications: false,
      riskAlerts: true,
      tradeAlerts: true,
      theme: 'dark',
      language: 'zh',
      autoRefresh: true,
      refreshInterval: 30,
      logLevel: 'info',
      dataRetention: 30,
      backupEnabled: true,
    });
    setHasChanges(false);
  };

  return (
    <Box>
      {/* 页面标题和操作 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
            系统设置
          </Typography>
          <Typography variant="body2" color="text.secondary">
            配置系统参数和偏好设置
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          {hasChanges && (
            <Chip
              label="有未保存的更改"
              color="warning"
              size="small"
            />
          )}
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleReset}
          >
            重置
          </Button>
          <Button
            variant="contained"
            startIcon={<Save />}
            onClick={handleSave}
            disabled={!hasChanges}
          >
            保存设置
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* 交易设置 */}
        <Grid item xs={12} md={6}>
          <Card
            sx={{
              background: 'rgba(26, 26, 26, 0.8)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 3,
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Security sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  交易设置
                </Typography>
              </Box>
              
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>默认交易对</InputLabel>
                    <Select
                      value={settings.defaultSymbol}
                      label="默认交易对"
                      onChange={(e) => handleSettingChange('defaultSymbol', e.target.value)}
                    >
                      <MenuItem value="BTC-USDT">BTC-USDT</MenuItem>
                      <MenuItem value="ETH-USDT">ETH-USDT</MenuItem>
                      <MenuItem value="SOL-USDT">SOL-USDT</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>默认时间框架</InputLabel>
                    <Select
                      value={settings.defaultTimeframe}
                      label="默认时间框架"
                      onChange={(e) => handleSettingChange('defaultTimeframe', e.target.value)}
                    >
                      <MenuItem value="1m">1分钟</MenuItem>
                      <MenuItem value="5m">5分钟</MenuItem>
                      <MenuItem value="15m">15分钟</MenuItem>
                      <MenuItem value="1H">1小时</MenuItem>
                      <MenuItem value="4H">4小时</MenuItem>
                      <MenuItem value="1D">1天</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="最大仓位比例"
                    type="number"
                    value={settings.maxPositionSize}
                    onChange={(e) => handleSettingChange('maxPositionSize', parseFloat(e.target.value))}
                    inputProps={{ min: 0, max: 1, step: 0.01 }}
                    helperText="0.2 = 20%"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>风险等级</InputLabel>
                    <Select
                      value={settings.riskLevel}
                      label="风险等级"
                      onChange={(e) => handleSettingChange('riskLevel', e.target.value)}
                    >
                      <MenuItem value="low">低风险</MenuItem>
                      <MenuItem value="medium">中等风险</MenuItem>
                      <MenuItem value="high">高风险</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.autoStart}
                        onChange={(e) => handleSettingChange('autoStart', e.target.checked)}
                      />
                    }
                    label="系统启动时自动开始交易"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* 风险设置 */}
        <Grid item xs={12} md={6}>
          <Card
            sx={{
              background: 'rgba(26, 26, 26, 0.8)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 3,
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Security sx={{ mr: 1, color: 'error.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  风险设置
                </Typography>
              </Box>
              
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="最大回撤 (%)"
                    type="number"
                    value={settings.maxDrawdown}
                    onChange={(e) => handleSettingChange('maxDrawdown', parseFloat(e.target.value))}
                    inputProps={{ min: 0, max: 100, step: 0.1 }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="止损比例 (%)"
                    type="number"
                    value={settings.stopLoss}
                    onChange={(e) => handleSettingChange('stopLoss', parseFloat(e.target.value))}
                    inputProps={{ min: 0, max: 100, step: 0.1 }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="止盈比例 (%)"
                    type="number"
                    value={settings.takeProfit}
                    onChange={(e) => handleSettingChange('takeProfit', parseFloat(e.target.value))}
                    inputProps={{ min: 0, max: 100, step: 0.1 }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="日最大损失 (%)"
                    type="number"
                    value={settings.maxDailyLoss}
                    onChange={(e) => handleSettingChange('maxDailyLoss', parseFloat(e.target.value))}
                    inputProps={{ min: 0, max: 100, step: 0.1 }}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* 通知设置 */}
        <Grid item xs={12} md={6}>
          <Card
            sx={{
              background: 'rgba(26, 26, 26, 0.8)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 3,
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Notifications sx={{ mr: 1, color: 'info.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  通知设置
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.emailNotifications}
                      onChange={(e) => handleSettingChange('emailNotifications', e.target.checked)}
                    />
                  }
                  label="邮件通知"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.pushNotifications}
                      onChange={(e) => handleSettingChange('pushNotifications', e.target.checked)}
                    />
                  }
                  label="推送通知"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.riskAlerts}
                      onChange={(e) => handleSettingChange('riskAlerts', e.target.checked)}
                    />
                  }
                  label="风险告警"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.tradeAlerts}
                      onChange={(e) => handleSettingChange('tradeAlerts', e.target.checked)}
                    />
                  }
                  label="交易通知"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* 界面设置 */}
        <Grid item xs={12} md={6}>
          <Card
            sx={{
              background: 'rgba(26, 26, 26, 0.8)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 3,
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Palette sx={{ mr: 1, color: 'secondary.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  界面设置
                </Typography>
              </Box>
              
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>主题</InputLabel>
                    <Select
                      value={settings.theme}
                      label="主题"
                      onChange={(e) => handleSettingChange('theme', e.target.value)}
                    >
                      <MenuItem value="dark">暗色主题</MenuItem>
                      <MenuItem value="light">亮色主题</MenuItem>
                      <MenuItem value="auto">跟随系统</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>语言</InputLabel>
                    <Select
                      value={settings.language}
                      label="语言"
                      onChange={(e) => handleSettingChange('language', e.target.value)}
                    >
                      <MenuItem value="zh">中文</MenuItem>
                      <MenuItem value="en">English</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.autoRefresh}
                        onChange={(e) => handleSettingChange('autoRefresh', e.target.checked)}
                      />
                    }
                    label="自动刷新数据"
                  />
                </Grid>
                {settings.autoRefresh && (
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="刷新间隔 (秒)"
                      type="number"
                      value={settings.refreshInterval}
                      onChange={(e) => handleSettingChange('refreshInterval', parseInt(e.target.value))}
                      inputProps={{ min: 5, max: 300 }}
                    />
                  </Grid>
                )}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* 系统设置 */}
        <Grid item xs={12}>
          <Card
            sx={{
              background: 'rgba(26, 26, 26, 0.8)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 3,
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Language sx={{ mr: 1, color: 'warning.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  系统设置
                </Typography>
              </Box>
              
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <FormControl fullWidth>
                    <InputLabel>日志级别</InputLabel>
                    <Select
                      value={settings.logLevel}
                      label="日志级别"
                      onChange={(e) => handleSettingChange('logLevel', e.target.value)}
                    >
                      <MenuItem value="debug">Debug</MenuItem>
                      <MenuItem value="info">Info</MenuItem>
                      <MenuItem value="warning">Warning</MenuItem>
                      <MenuItem value="error">Error</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <TextField
                    fullWidth
                    label="数据保留天数"
                    type="number"
                    value={settings.dataRetention}
                    onChange={(e) => handleSettingChange('dataRetention', parseInt(e.target.value))}
                    inputProps={{ min: 7, max: 365 }}
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.backupEnabled}
                        onChange={(e) => handleSettingChange('backupEnabled', e.target.checked)}
                      />
                    }
                    label="启用自动备份"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    fullWidth
                    variant="outlined"
                    color="error"
                    onClick={() => console.log('清除缓存')}
                  >
                    清除缓存
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 保存提示 */}
      {hasChanges && (
        <Alert severity="info" sx={{ mt: 3 }}>
          <Typography variant="body2">
            您有未保存的设置更改。请点击"保存设置"按钮来保存您的更改。
          </Typography>
        </Alert>
      )}
    </Box>
  );
};

export default Settings;
