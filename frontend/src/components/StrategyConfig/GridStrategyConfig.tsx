import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Button,
  Slider,
  Chip,
  Alert,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Info as InfoIcon,
  Save as SaveIcon,
  Preview as PreviewIcon,
  RestartAlt as ResetIcon,
} from '@mui/icons-material';

interface GridConfig {
  strategy_id: string;
  strategy_name: string;
  symbol: string;
  base_quantity: number;
  grid_type: 'ARITHMETIC' | 'GEOMETRIC' | 'FIBONACCI' | 'CUSTOM';
  grid_direction: 'BOTH' | 'UP_ONLY' | 'DOWN_ONLY';
  grid_count: number;
  grid_spacing: number;
  center_price?: number;
  upper_price?: number;
  lower_price?: number;
  max_position: number;
  stop_loss_price?: number;
  take_profit_price?: number;
  max_drawdown: number;
  total_capital: number;
  position_ratio: number;
  reserve_ratio: number;
  commission_rate: number;
  slippage: number;
  min_trade_amount: number;
  enable_dynamic_adjustment: boolean;
  adjustment_threshold: number;
  rebalance_interval: number;
  enable_trailing_stop: boolean;
  trailing_stop_distance: number;
  enable_partial_fill: boolean;
  max_partial_fills: number;
}

interface GridStrategyConfigProps {
  config: GridConfig;
  onChange: (config: GridConfig) => void;
  onPreview: () => void;
  onSave: () => void;
  onReset: () => void;
  isPreviewMode?: boolean;
}

const GridStrategyConfig: React.FC<GridStrategyConfigProps> = ({
  config,
  onChange,
  onPreview,
  onSave,
  onReset,
  isPreviewMode = false,
}) => {
  const [expandedSections, setExpandedSections] = useState<string[]>(['basic']);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  // 配置模板
  const configTemplates = {
    conservative: {
      grid_count: 5,
      grid_spacing: 0.02,
      position_ratio: 0.6,
      reserve_ratio: 0.4,
      max_drawdown: 0.03,
      adjustment_threshold: 0.05,
    },
    moderate: {
      grid_count: 10,
      grid_spacing: 0.01,
      position_ratio: 0.8,
      reserve_ratio: 0.2,
      max_drawdown: 0.05,
      adjustment_threshold: 0.02,
    },
    aggressive: {
      grid_count: 20,
      grid_spacing: 0.005,
      position_ratio: 0.9,
      reserve_ratio: 0.1,
      max_drawdown: 0.08,
      adjustment_threshold: 0.01,
    },
  };

  const handleSectionToggle = (section: string) => {
    setExpandedSections(prev =>
      prev.includes(section)
        ? prev.filter(s => s !== section)
        : [...prev, section]
    );
  };

  const handleConfigChange = (field: keyof GridConfig, value: any) => {
    const newConfig = { ...config, [field]: value };
    onChange(newConfig);
    
    // 清除相关验证错误
    if (validationErrors[field]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const handleTemplateApply = (template: keyof typeof configTemplates) => {
    const templateConfig = configTemplates[template];
    const newConfig = { ...config, ...templateConfig };
    onChange(newConfig);
  };

  const validateConfig = (): boolean => {
    const errors: Record<string, string> = {};

    // 基础验证
    if (!config.strategy_name.trim()) {
      errors.strategy_name = '策略名称不能为空';
    }
    if (!config.symbol.trim()) {
      errors.symbol = '交易对不能为空';
    }
    if (config.base_quantity <= 0) {
      errors.base_quantity = '基础交易数量必须大于0';
    }
    if (config.total_capital <= 0) {
      errors.total_capital = '总资金必须大于0';
    }
    if (config.grid_count <= 0) {
      errors.grid_count = '网格数量必须大于0';
    }
    if (config.grid_spacing <= 0 || config.grid_spacing > 1) {
      errors.grid_spacing = '网格间距必须在0-1之间';
    }
    if (config.position_ratio <= 0 || config.position_ratio > 1) {
      errors.position_ratio = '仓位比例必须在0-1之间';
    }
    if (config.reserve_ratio < 0 || config.reserve_ratio > 1) {
      errors.reserve_ratio = '预留比例必须在0-1之间';
    }
    if (config.position_ratio + config.reserve_ratio > 1) {
      errors.reserve_ratio = '仓位比例和预留比例之和不能超过1';
    }
    if (config.max_drawdown <= 0 || config.max_drawdown > 1) {
      errors.max_drawdown = '最大回撤限制必须在0-1之间';
    }

    // 价格范围验证
    if (config.upper_price && config.lower_price) {
      if (config.upper_price <= config.lower_price) {
        errors.upper_price = '上限价格必须大于下限价格';
      }
    }

    // 止损止盈验证
    if (config.stop_loss_price && config.take_profit_price) {
      if (config.stop_loss_price >= config.take_profit_price) {
        errors.stop_loss_price = '止损价格必须小于止盈价格';
      }
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handlePreview = () => {
    if (validateConfig()) {
      onPreview();
    }
  };

  const handleSave = () => {
    if (validateConfig()) {
      onSave();
    }
  };

  const renderBasicConfig = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="策略名称"
          value={config.strategy_name}
          onChange={(e) => handleConfigChange('strategy_name', e.target.value)}
          error={!!validationErrors.strategy_name}
          helperText={validationErrors.strategy_name}
          disabled={isPreviewMode}
        />
      </Grid>
      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="交易对"
          value={config.symbol}
          onChange={(e) => handleConfigChange('symbol', e.target.value.toUpperCase())}
          error={!!validationErrors.symbol}
          helperText={validationErrors.symbol}
          disabled={isPreviewMode}
        />
      </Grid>
      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="总资金"
          type="number"
          value={config.total_capital}
          onChange={(e) => handleConfigChange('total_capital', parseFloat(e.target.value) || 0)}
          error={!!validationErrors.total_capital}
          helperText={validationErrors.total_capital}
          disabled={isPreviewMode}
        />
      </Grid>
      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="基础交易数量"
          type="number"
          value={config.base_quantity}
          onChange={(e) => handleConfigChange('base_quantity', parseFloat(e.target.value) || 0)}
          error={!!validationErrors.base_quantity}
          helperText={validationErrors.base_quantity}
          disabled={isPreviewMode}
        />
      </Grid>
    </Grid>
  );

  const renderGridConfig = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <FormControl fullWidth>
          <InputLabel>网格类型</InputLabel>
          <Select
            value={config.grid_type}
            onChange={(e) => handleConfigChange('grid_type', e.target.value)}
            disabled={isPreviewMode}
          >
            <MenuItem value="ARITHMETIC">等差数列</MenuItem>
            <MenuItem value="GEOMETRIC">等比数列</MenuItem>
            <MenuItem value="FIBONACCI">斐波那契</MenuItem>
            <MenuItem value="CUSTOM">自定义</MenuItem>
          </Select>
        </FormControl>
      </Grid>
      <Grid item xs={12} md={6}>
        <FormControl fullWidth>
          <InputLabel>网格方向</InputLabel>
          <Select
            value={config.grid_direction}
            onChange={(e) => handleConfigChange('grid_direction', e.target.value)}
            disabled={isPreviewMode}
          >
            <MenuItem value="BOTH">双向</MenuItem>
            <MenuItem value="UP_ONLY">仅向上</MenuItem>
            <MenuItem value="DOWN_ONLY">仅向下</MenuItem>
          </Select>
        </FormControl>
      </Grid>
      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="网格数量"
          type="number"
          value={config.grid_count}
          onChange={(e) => handleConfigChange('grid_count', parseInt(e.target.value) || 0)}
          error={!!validationErrors.grid_count}
          helperText={validationErrors.grid_count}
          disabled={isPreviewMode}
        />
      </Grid>
      <Grid item xs={12} md={6}>
        <Box>
          <Typography gutterBottom>
            网格间距: {config.grid_spacing * 100}%
          </Typography>
          <Slider
            value={config.grid_spacing}
            onChange={(_, value) => handleConfigChange('grid_spacing', value as number)}
            min={0.001}
            max={0.1}
            step={0.001}
            disabled={isPreviewMode}
          />
        </Box>
      </Grid>
      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="中心价格"
          type="number"
          value={config.center_price || ''}
          onChange={(e) => handleConfigChange('center_price', parseFloat(e.target.value) || undefined)}
          disabled={isPreviewMode}
        />
      </Grid>
      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="上限价格"
          type="number"
          value={config.upper_price || ''}
          onChange={(e) => handleConfigChange('upper_price', parseFloat(e.target.value) || undefined)}
          error={!!validationErrors.upper_price}
          helperText={validationErrors.upper_price}
          disabled={isPreviewMode}
        />
      </Grid>
      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="下限价格"
          type="number"
          value={config.lower_price || ''}
          onChange={(e) => handleConfigChange('lower_price', parseFloat(e.target.value) || undefined)}
          disabled={isPreviewMode}
        />
      </Grid>
    </Grid>
  );

  const renderRiskConfig = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Box>
          <Typography gutterBottom>
            仓位比例: {config.position_ratio * 100}%
          </Typography>
          <Slider
            value={config.position_ratio}
            onChange={(_, value) => handleConfigChange('position_ratio', value as number)}
            min={0.1}
            max={1.0}
            step={0.01}
            disabled={isPreviewMode}
          />
        </Box>
      </Grid>
      <Grid item xs={12} md={6}>
        <Box>
          <Typography gutterBottom>
            预留比例: {config.reserve_ratio * 100}%
          </Typography>
          <Slider
            value={config.reserve_ratio}
            onChange={(_, value) => handleConfigChange('reserve_ratio', value as number)}
            min={0.0}
            max={1.0 - config.position_ratio}
            step={0.01}
            disabled={isPreviewMode}
          />
        </Box>
      </Grid>
      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="最大持仓"
          type="number"
          value={config.max_position}
          onChange={(e) => handleConfigChange('max_position', parseFloat(e.target.value) || 0)}
          disabled={isPreviewMode}
        />
      </Grid>
      <Grid item xs={12} md={6}>
        <Box>
          <Typography gutterBottom>
            最大回撤: {config.max_drawdown * 100}%
          </Typography>
          <Slider
            value={config.max_drawdown}
            onChange={(_, value) => handleConfigChange('max_drawdown', value as number)}
            min={0.01}
            max={0.2}
            step={0.01}
            disabled={isPreviewMode}
          />
        </Box>
      </Grid>
      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="止损价格"
          type="number"
          value={config.stop_loss_price || ''}
          onChange={(e) => handleConfigChange('stop_loss_price', parseFloat(e.target.value) || undefined)}
          error={!!validationErrors.stop_loss_price}
          helperText={validationErrors.stop_loss_price}
          disabled={isPreviewMode}
        />
      </Grid>
      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="止盈价格"
          type="number"
          value={config.take_profit_price || ''}
          onChange={(e) => handleConfigChange('take_profit_price', parseFloat(e.target.value) || undefined)}
          disabled={isPreviewMode}
        />
      </Grid>
    </Grid>
  );

  const renderAdvancedConfig = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="手续费率"
          type="number"
          value={config.commission_rate}
          onChange={(e) => handleConfigChange('commission_rate', parseFloat(e.target.value) || 0)}
          disabled={isPreviewMode}
        />
      </Grid>
      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="滑点"
          type="number"
          value={config.slippage}
          onChange={(e) => handleConfigChange('slippage', parseFloat(e.target.value) || 0)}
          disabled={isPreviewMode}
        />
      </Grid>
      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="最小交易金额"
          type="number"
          value={config.min_trade_amount}
          onChange={(e) => handleConfigChange('min_trade_amount', parseFloat(e.target.value) || 0)}
          disabled={isPreviewMode}
        />
      </Grid>
      <Grid item xs={12} md={6}>
        <FormControlLabel
          control={
            <Switch
              checked={config.enable_dynamic_adjustment}
              onChange={(e) => handleConfigChange('enable_dynamic_adjustment', e.target.checked)}
              disabled={isPreviewMode}
            />
          }
          label="启用动态调整"
        />
      </Grid>
      {config.enable_dynamic_adjustment && (
        <>
          <Grid item xs={12} md={6}>
            <Box>
              <Typography gutterBottom>
                调整阈值: {config.adjustment_threshold * 100}%
              </Typography>
              <Slider
                value={config.adjustment_threshold}
                onChange={(_, value) => handleConfigChange('adjustment_threshold', value as number)}
                min={0.01}
                max={0.1}
                step={0.01}
                disabled={isPreviewMode}
              />
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="重新平衡间隔(秒)"
              type="number"
              value={config.rebalance_interval}
              onChange={(e) => handleConfigChange('rebalance_interval', parseInt(e.target.value) || 0)}
              disabled={isPreviewMode}
            />
          </Grid>
        </>
      )}
      <Grid item xs={12} md={6}>
        <FormControlLabel
          control={
            <Switch
              checked={config.enable_trailing_stop}
              onChange={(e) => handleConfigChange('enable_trailing_stop', e.target.checked)}
              disabled={isPreviewMode}
            />
          }
          label="启用跟踪止损"
        />
      </Grid>
      {config.enable_trailing_stop && (
        <Grid item xs={12} md={6}>
          <Box>
            <Typography gutterBottom>
              跟踪止损距离: {config.trailing_stop_distance * 100}%
            </Typography>
            <Slider
              value={config.trailing_stop_distance}
              onChange={(_, value) => handleConfigChange('trailing_stop_distance', value as number)}
              min={0.01}
              max={0.1}
              step={0.01}
              disabled={isPreviewMode}
            />
          </Box>
        </Grid>
      )}
    </Grid>
  );

  return (
    <Box>
      {/* 配置模板 */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            配置模板
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Chip
              label="保守型"
              onClick={() => handleTemplateApply('conservative')}
              disabled={isPreviewMode}
              color="success"
              variant="outlined"
            />
            <Chip
              label="稳健型"
              onClick={() => handleTemplateApply('moderate')}
              disabled={isPreviewMode}
              color="primary"
              variant="outlined"
            />
            <Chip
              label="激进型"
              onClick={() => handleTemplateApply('aggressive')}
              disabled={isPreviewMode}
              color="warning"
              variant="outlined"
            />
          </Box>
        </CardContent>
      </Card>

      {/* 配置表单 */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">网格交易策略配置</Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                startIcon={<ResetIcon />}
                onClick={onReset}
                disabled={isPreviewMode}
              >
                重置
              </Button>
              <Button
                variant="outlined"
                startIcon={<PreviewIcon />}
                onClick={handlePreview}
                disabled={isPreviewMode}
              >
                预览
              </Button>
              <Button
                variant="contained"
                startIcon={<SaveIcon />}
                onClick={handleSave}
                disabled={isPreviewMode}
              >
                保存
              </Button>
            </Box>
          </Box>

          {/* 基础配置 */}
          <Accordion
            expanded={expandedSections.includes('basic')}
            onChange={() => handleSectionToggle('basic')}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">基础配置</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {renderBasicConfig()}
            </AccordionDetails>
          </Accordion>

          {/* 网格配置 */}
          <Accordion
            expanded={expandedSections.includes('grid')}
            onChange={() => handleSectionToggle('grid')}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">网格配置</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {renderGridConfig()}
            </AccordionDetails>
          </Accordion>

          {/* 风险配置 */}
          <Accordion
            expanded={expandedSections.includes('risk')}
            onChange={() => handleSectionToggle('risk')}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">风险配置</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {renderRiskConfig()}
            </AccordionDetails>
          </Accordion>

          {/* 高级配置 */}
          <Accordion
            expanded={expandedSections.includes('advanced')}
            onChange={() => handleSectionToggle('advanced')}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">高级配置</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {renderAdvancedConfig()}
            </AccordionDetails>
          </Accordion>

          {/* 验证错误显示 */}
          {Object.keys(validationErrors).length > 0 && (
            <Alert severity="error" sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                配置验证失败：
              </Typography>
              <ul>
                {Object.entries(validationErrors).map(([field, error]) => (
                  <li key={field}>{error}</li>
                ))}
              </ul>
            </Alert>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default GridStrategyConfig;
