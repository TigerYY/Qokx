import React, { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TablePagination,
  TableSortLabel,
  Chip,
  IconButton,
  Tooltip,
  Box,
  Typography,
} from '@mui/material';
import {
  Visibility as ViewIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreIcon,
} from '@mui/icons-material';

export interface Column {
  id: string;
  label: string;
  minWidth?: number;
  align?: 'right' | 'left' | 'center';
  sortable?: boolean;
  format?: (value: any, row?: any) => React.ReactNode;
}

interface DataTableProps {
  columns: Column[];
  data: any[];
  page: number;
  rowsPerPage: number;
  totalRows: number;
  onPageChange: (page: number) => void;
  onRowsPerPageChange: (rowsPerPage: number) => void;
  onSort?: (field: string, direction: 'asc' | 'desc') => void;
  sortField?: string;
  sortDirection?: 'asc' | 'desc';
  actions?: {
    view?: (row: any) => void;
    edit?: (row: any) => void;
    delete?: (row: any) => void;
  };
  loading?: boolean;
}

const DataTable: React.FC<DataTableProps> = ({
  columns,
  data,
  page,
  rowsPerPage,
  totalRows,
  onPageChange,
  onRowsPerPageChange,
  onSort,
  sortField,
  sortDirection = 'asc',
  actions,
  loading = false,
}) => {
  const [hoveredRow, setHoveredRow] = useState<number | null>(null);

  const handleSort = (field: string) => {
    if (onSort) {
      const direction = sortField === field && sortDirection === 'asc' ? 'desc' : 'asc';
      onSort(field, direction);
    }
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    onPageChange(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    onRowsPerPageChange(parseInt(event.target.value, 10));
  };

  const formatCellValue = (value: any, format?: (value: any, row?: any) => React.ReactNode, row?: any) => {
    if (format) {
      return format(value, row);
    }
    return value;
  };

  return (
    <Paper
      sx={{
        background: 'rgba(26, 26, 26, 0.8)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: 3,
        overflow: 'hidden',
      }}
    >
      <TableContainer sx={{ maxHeight: 600 }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              {columns.map((column) => (
                <TableCell
                  key={column.id}
                  align={column.align}
                  style={{ minWidth: column.minWidth }}
                  sx={{
                    backgroundColor: 'rgba(0, 212, 170, 0.05)',
                    color: 'text.primary',
                    fontWeight: 600,
                    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                >
                  {column.sortable ? (
                    <TableSortLabel
                      active={sortField === column.id}
                      direction={sortField === column.id ? sortDirection : 'asc'}
                      onClick={() => handleSort(column.id)}
                      sx={{
                        color: 'text.primary',
                        '&.Mui-active': {
                          color: 'primary.main',
                        },
                        '&:hover': {
                          color: 'primary.main',
                        },
                      }}
                    >
                      {column.label}
                    </TableSortLabel>
                  ) : (
                    column.label
                  )}
                </TableCell>
              ))}
              {actions && (
                <TableCell
                  align="center"
                  sx={{
                    backgroundColor: 'rgba(0, 212, 170, 0.05)',
                    color: 'text.primary',
                    fontWeight: 600,
                    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                    minWidth: 100,
                  }}
                >
                  操作
                </TableCell>
              )}
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={columns.length + (actions ? 1 : 0)} align="center">
                  <Box sx={{ py: 4 }}>
                    <Typography color="text.secondary">加载中...</Typography>
                  </Box>
                </TableCell>
              </TableRow>
            ) : data.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length + (actions ? 1 : 0)} align="center">
                  <Box sx={{ py: 4 }}>
                    <Typography color="text.secondary">暂无数据</Typography>
                  </Box>
                </TableCell>
              </TableRow>
            ) : (
              data.map((row, index) => (
                <TableRow
                  key={index}
                  hover
                  onMouseEnter={() => setHoveredRow(index)}
                  onMouseLeave={() => setHoveredRow(null)}
                  sx={{
                    '&:hover': {
                      backgroundColor: 'rgba(0, 212, 170, 0.05)',
                    },
                    '&:nth-of-type(odd)': {
                      backgroundColor: 'rgba(255, 255, 255, 0.02)',
                    },
                  }}
                >
                  {columns.map((column) => (
                    <TableCell
                      key={column.id}
                      align={column.align}
                      sx={{
                        color: 'text.primary',
                        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                      }}
                    >
                      {formatCellValue(row[column.id], column.format, row)}
                    </TableCell>
                  ))}
                  {actions && (
                    <TableCell
                      align="center"
                      sx={{
                        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                      }}
                    >
                      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 0.5 }}>
                        {actions.view && (
                          <Tooltip title="查看">
                            <IconButton
                              size="small"
                              onClick={() => actions.view!(row)}
                              sx={{ color: 'primary.main' }}
                            >
                              <ViewIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                        {actions.edit && (
                          <Tooltip title="编辑">
                            <IconButton
                              size="small"
                              onClick={() => actions.edit!(row)}
                              sx={{ color: 'warning.main' }}
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                        {actions.delete && (
                          <Tooltip title="删除">
                            <IconButton
                              size="small"
                              onClick={() => actions.delete!(row)}
                              sx={{ color: 'error.main' }}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                      </Box>
                    </TableCell>
                  )}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        rowsPerPageOptions={[10, 25, 50, 100]}
        component="div"
        count={totalRows}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
        sx={{
          backgroundColor: 'rgba(0, 212, 170, 0.02)',
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          color: 'text.primary',
        }}
      />
    </Paper>
  );
};

export default DataTable;
