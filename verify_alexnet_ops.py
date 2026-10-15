import torch
import torch.nn as nn

from fvcore.nn import FlopCountAnalysis, parameter_count_table


class OriginalAlexNet(nn.Module):
    def __init__(self, num_classes=1000):
        super().__init__()

        self.features = nn.Sequential(
            # 227 -> 55
            nn.Conv2d(
                3, 96,
                kernel_size=11,
                stride=4,
                padding=0,
            ),
            nn.ReLU(inplace=False),
            nn.LocalResponseNorm(
                size=5,
                alpha=1e-4,
                beta=0.75,
                k=2,
            ),
            nn.MaxPool2d(
                kernel_size=3,
                stride=2,
            ),

            # 27 -> 27
            nn.Conv2d(
                96, 256,
                kernel_size=5,
                padding=2,
                groups=2,
            ),
            nn.ReLU(inplace=False),
            nn.LocalResponseNorm(
                size=5,
                alpha=1e-4,
                beta=0.75,
                k=2,
            ),
            nn.MaxPool2d(
                kernel_size=3,
                stride=2,
            ),

            nn.Conv2d(
                256, 384,
                kernel_size=3,
                padding=1,
            ),
            nn.ReLU(inplace=False),

            nn.Conv2d(
                384, 384,
                kernel_size=3,
                padding=1,
                groups=2,
            ),
            nn.ReLU(inplace=False),

            nn.Conv2d(
                384, 256,
                kernel_size=3,
                padding=1,
                groups=2,
            ),
            nn.ReLU(inplace=False),

            nn.MaxPool2d(
                kernel_size=3,
                stride=2,
            ),
        )

        self.classifier = nn.Sequential(
            nn.Dropout(),
            nn.Linear(256 * 6 * 6, 4096),
            nn.ReLU(inplace=False),
            nn.Dropout(),
            nn.Linear(4096, 4096),
            nn.ReLU(inplace=False),
            nn.Linear(4096, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        x = torch.flatten(x, 1)
        return self.classifier(x)


model = OriginalAlexNet().eval()
x = torch.randn(1, 3, 227, 227)

with torch.no_grad():
    y = model(x)

print("Output shape:", tuple(y.shape))

analysis = FlopCountAnalysis(model, x)

print("\nTotal FVCore count:")
print(f"{analysis.total():,.0f}")

print("\nCount by module:")
for name, count in analysis.by_module().items():
    if count > 0:
        print(f"{name:<30} {count:>15,.0f}")

print("\nParameters:")
print(parameter_count_table(model))
