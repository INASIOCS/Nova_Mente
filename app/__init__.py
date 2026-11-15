"""NovaMente — Sistema Inteligente de Adaptação e Geração de Conteúdo Educacional."""

import warnings

# O SDK `google-generativeai` emite um FutureWarning de descontinuação a cada
# import. A migração para `google-genai` está registrada como dívida técnica no
# HANDOFF.md; até lá, silenciamos o aviso para não poluir os logs do pipeline.
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    module=r"google\.generativeai.*",
)

__version__ = "1.0.0"
