# Which control absorbs the raw digital-expert association?
suppressMessages(library(fixest))
source_lines <- readLines("scripts/12_first_models.R")
eval(parse(text = source_lines[3:16]))
s2 <- subset(s, !is.na(indep_sh) & !is.na(state) & !is.na(bsize))
f <- list(
  raw_same_sample = ai_any ~ dig_any | cy,
  plus_sector     = ai_any ~ dig_any | cy + sector_group,
  plus_size       = ai_any ~ dig_any + log_assets | cy + sector_group,
  plus_length     = ai_any ~ dig_any + log_assets + log_chars | cy + sector_group,
  full            = ai_any ~ dig_any + log_assets + log_chars + bsize + indep_sh + state | cy + sector_group)
for (n in names(f)) {
  m <- feols(f[[n]], s2, cluster = ~firm)
  ct <- coeftable(m)["dig_any", ]
  cat(sprintf("%-16s n=%d  dig_any=%.3f  se=%.3f  p=%.3f\n", n, nobs(m), ct[1], ct[2], ct[4]))
}
m <- feols(ai_any ~ dig_any + log_assets + log_chars | cy + sector_group, s, cluster = ~firm)
ct <- coeftable(m)["dig_any", ]
cat(sprintf("size+length, larger sample n=%d dig_any=%.3f se=%.3f p=%.3f\n", nobs(m), ct[1], ct[2], ct[4]))
cat("\nAI share by sector x expert (larger sample):\n"); print(round(tapply(s$ai_any, list(s$sector_group, s$dig_any), mean), 2))
print(table(s$sector_group, s$dig_any))
