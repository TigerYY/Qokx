import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
} from '@mui/material';
import { TrendingUp, TrendingDown } from '@mui/icons-material';

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  progress?: number;
  icon?: React.ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
  trend?: 'up' | 'down' | 'neutral';
  subtitle?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  changeLabel,
  progress,
  icon,
  color = 'primary',
  trend = 'neutral',
  subtitle,
}) => {
  const getTrendIcon = () => {
    if (trend === 'up') return <TrendingUp sx={{ fontSize: 16 }} />;
    if (trend === 'down') return <TrendingDown sx={{ fontSize: 16 }} />;
    return null;
  };

  const getTrendColor = () => {
    if (trend === 'up') return 'success.main';
    if (trend === 'down') return 'error.main';
    return 'text.secondary';
  };

  const formatValue = (val: string | number) => {
    if (typeof val === 'number') {
      if (val >= 1000000) {
        return `${(val / 1000000).toFixed(1)}M`;
      }
      if (val >= 1000) {
        return `${(val / 1000).toFixed(1)}K`;
      }
      return val.toLocaleString();
    }
    return val;
  };

  return (
    <Card
      sx={{
        background: 'rgba(26, 26, 26, 0.8)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: 3,
        height: '100%',
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: '0 8px 32px rgba(0, 212, 170, 0.1)',
        },
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          {icon && (
            <Box
              sx={{
                p: 1,
                borderRadius: 2,
                backgroundColor: `${color}.main`,
                color: 'white',
                mr: 2,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {icon}
            </Box>
          )}
          <Box sx={{ flexGrow: 1 }}>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ fontWeight: 500, mb: 0.5 }}
            >
              {title}
            </Typography>
            {subtitle && (
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ display: 'block' }}
              >
                {subtitle}
              </Typography>
            )}
          </Box>
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography
            variant="h4"
            sx={{
              fontWeight: 700,
              color: 'text.primary',
              mb: 1,
            }}
          >
            {formatValue(value)}
          </Typography>

          {change !== undefined && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Chip
                icon={getTrendIcon() || undefined}
                label={`${change > 0 ? '+' : ''}${change.toFixed(2)}%`}
                size="small"
                sx={{
                  backgroundColor: getTrendColor(),
                  color: 'white',
                  fontWeight: 600,
                }}
              />
              {changeLabel && (
                <Typography variant="caption" color="text.secondary">
                  {changeLabel}
                </Typography>
              )}
            </Box>
          )}
        </Box>

        {progress !== undefined && (
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="caption" color="text.secondary">
                进度
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {progress.toFixed(1)}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={progress}
              sx={{
                height: 6,
                borderRadius: 3,
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: `${color}.main`,
                  borderRadius: 3,
                },
              }}
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default MetricCard;
